#!/usr/bin/env bash
# Script for installing complete stack and all projects necessary to run
# Gaussino with AdePT.

root="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"
lcg_version="LCG_105c"
lcg_platform="x86_64-el9-gcc13-opt"
binary_tag="x86_64_v3-el9-gcc13+cuda12_4-opt+g"
build_dir="build.$binary_tag"
install_dir="InstallArea/$binary_tag"
cuda_architecture=89
num_threads=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
export CUDACXX=$(which nvcc)

# 0. Setup the environment
source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh $lcg_version $lcg_platform

# 1. Organize stack folder with lb-stack-setup
if [ ! -d stack ]; then
	curl https://gitlab.cern.ch/rmatev/lb-stack-setup/raw/master/setup.py | python3 - stack
fi

cd stack
python utils/config.py binaryTag $binary_tag
python utils/config.py forwardEnv '["DISPLAY","SSH_AUTH_SOCK","SSH_AGENT_PID","GITCONDDBPATH","X509_USER_PROXY","CUDACXX"]'
python utils/config.py dataPackages '["DBASE/AppConfig","DBASE/PRConfig","PARAM/ParamFiles","DBASE/SprucingConfig","PARAM/Geant4Files"]'

# 2. Install AdePT

# 2.1. Install VecCore
veccore_install="$root/stack/VecCore/$install_dir"

if [ ! -d VecCore ]; then
	git clone https://github.com/root-project/veccore.git VecCore
fi

cd VecCore
git checkout v0.8.2
cmake -S. -B $build_dir -DCMAKE_INSTALL_PREFIX="$veccore_install"
cmake --build $build_dir --target install
cd ..

# 2.2. Install VecGeom
vecgeom_install="$root/stack/VecGeom/$install_dir"

if [ ! -d VecGeom ]; then
	git clone ssh://git@gitlab.cern.ch:7999/VecGeom/VecGeom.git
fi

cd VecGeom
git checkout v2.0.0-rc.3
cmake -S. -B $build_dir -DCMAKE_INSTALL_PREFIX="$vecgeom_install" \
    -DCMAKE_PREFIX_PATH="$veccore_install" \
    -DVECGEOM_ENABLE_CUDA=ON \
    -DVECGEOM_GDML=ON \
    -DBACKEND=Scalar \
    -DCMAKE_CUDA_ARCHITECTURES=$cuda_architecture \
    -DVECGEOM_USE_NAVINDEX=ON \
    -DCMAKE_BUILD_TYPE=Release
cmake --build $build_dir --target install -- -j$num_threads
cd ..

# 2.3. Install Geant4
geant4_install="$root/stack/Geant4/$install_dir"
make Geant4 BUILDFLAGS="-j6"

# 2.4. Install G4HepEm
g4hepem_install="$root/stack/G4HepEm/$install_dir"

if [ ! -d G4HepEm ]; then
	git clone https://github.com/mnovak42/g4hepem.git G4HepEm
fi

cd G4HepEm
git checkout 20250220

## G4HepEm expects Geant4 v11 to be installed, but LHCb currently uses v10.7. However,
## there is a patch that implements the tracking interface for Geant4 v10.7 so we can
## use it.
sed -i 's/11.0/10.7/g' ./G4HepEm/G4HepEm/CMakeLists.txt

cmake -S. -B $build_dir -DCMAKE_INSTALL_PREFIX="$g4hepem_install" \
    -DCMAKE_PREFIX_PATH="$geant4_install" \
    -DG4HepEm_CUDA_BUILD=ON \
    -DG4HepEm_EARLY_TRACKING_EXIT=ON
cmake --build $build_dir --target install -- -j$num_threads
cd ..

# 2.5. Install AdePT
adept_install="$root/stack/AdePT/$install_dir"

if [ ! -d AdePT ]; then
	git clone https://github.com/apt-sim/AdePT.git
fi

cd AdePT
cmake -S. -B $build_dir -DCMAKE_INSTALL_PREFIX="$adept_install" \
    -DCMAKE_PREFIX_PATH="$veccore_install;$vecgeom_install;$g4hepem_install;$geant4_install" \
    -DCMAKE_CUDA_ARCHITECTURES=$cuda_architecture \
    -DWITH_FLUCT=OFF \
    -DBUILD_TESTING=OFF \
    -DASYNC_MODE=ON \
    -DCMAKE_BUILD_TYPE=Release
cmake --build $build_dir --target install -- -j$num_threads
cd ..

# 3. Install Gaussino
gaussino_install="$root/stack/Gaussino/$install_dir"

if [ ! -d Gaussino ]; then
	make Gaussino/checkout
	cd Gaussino
	git checkout jbenavid-adept-integration
	cd ..
fi
python utils/config.py -- cmakeFlags.Gaussino "-DWITH_ADEPT=ON -DAdePT_DIR=$adept_install/lib64/cmake/AdePT -DG4VG_DIR=$adept_install/lib64/cmake/G4VG"
make Gaussino BUILDFLAGS="-j$num_threads"
