"""Simple example of a simulation with Gaussino"""

import os

from GaudiKernel import SystemOfUnits as units
from Configurables import (
    ApplicationMgr,
    Gaussino,
    GaussinoGeneration,
    GaussinoGeometry,
    ParticleGun,
    FixedMomentum,
    FlatSmearVertex,
    FlatNParticles,
    ExternalDetectorEmbedder,
    CalorimeterMonitoring,
)
from ExternalDetector.Materials import OUTER_SPACE


particle_types = {
    "proton": 2212,
    "electron": 11,
    "gamma": 22,
}

# Parameters
particles_per_event = int(os.environ.get("PARTICLES_PER_EVENT", 100))
nthreads = int(os.environ.get("NUMBER_OF_THREADS", 1))
particle_type = particle_types.get(os.environ.get("PARTICLE_TYPE", "electron"), 11)
number_of_events = int(os.environ.get("NUMBER_OF_EVENTS", 10))
particle_energy = float(os.environ.get("PARTICLE_ENERGY_MEV", 10.0)) * units.MeV

## constants
n_layers = 10
absorber_thickness = 10 * units.mm
gap_thickness = 5 * units.mm

calor_size_xy = 10 * units.cm

calor_thickness = n_layers * (absorber_thickness + gap_thickness)

world_length = 1.2 * calor_thickness

# General Gaussino configs
Gaussino().EvtMax = number_of_events
Gaussino().Phases = ["Generator", "Simulation"]
Gaussino().EnableHive = True
Gaussino().ThreadPoolSize = nthreads
Gaussino().EventSlots = nthreads


# Setup the generation phase by defining a Particle Gun
def setup_particle_gun(
    *, number_of_particles, particle_energy, particle_type, gun_position
):
    GaussinoGeneration().ParticleGun = True
    pgun = ParticleGun("ParticleGun")
    pgun.addTool(FixedMomentum, name="FixedMomentum")
    pgun.ParticleGunTool = "FixedMomentum"
    pgun.addTool(FlatNParticles, name="FlatNParticles")
    pgun.NumberOfParticlesTool = "FlatNParticles"
    pgun.FlatNParticles.MinNParticles = number_of_particles
    pgun.FlatNParticles.MaxNParticles = number_of_particles
    pgun.FixedMomentum.px = 0.0 * units.GeV
    pgun.FixedMomentum.py = 0.0 * units.GeV
    pgun.FixedMomentum.pz = particle_energy
    pgun.FixedMomentum.PdgCodes = [particle_type]

    pgun.addTool(FlatSmearVertex, name="FlatSmearVertex")
    pgun.FlatSmearVertex.xVertexMin = 0.0 * units.mm
    pgun.FlatSmearVertex.xVertexMax = 0.0 * units.mm
    pgun.FlatSmearVertex.yVertexMin = 0.0 * units.mm
    pgun.FlatSmearVertex.yVertexMax = 0.0 * units.mm
    pgun.FlatSmearVertex.zVertexMin = gun_position
    pgun.FlatSmearVertex.zVertexMax = gun_position


# Some useful particle codes
# 2212: Proton
# 11: Electron
# 22: Gamma
setup_particle_gun(
    number_of_particles=particles_per_event,
    particle_energy=particle_energy,
    particle_type=particle_type,
    gun_position=-0.5 * world_length,
)


########################
#    Setup Geometry    #
########################
def setup_geometry(
    *,
    emb_name="ExternalDetectorEmbedder",
    n_layers=10,
    calor_size_xy=None,
    absorber_thickness=None,
    gap_thickness=None,
    default_material="OUTER_SPACE",
    gap_material="liquidArgon",
    absorber_material="G4_Pb",
):
    GaussinoGeometry().ExternalDetectorEmbedder = emb_name
    external = ExternalDetectorEmbedder(emb_name)

    # Sizes
    layer_thickness = absorber_thickness + gap_thickness
    calor_thickness = layer_thickness * n_layers
    world_size_XY = 1.2 * calor_size_xy
    world_size_Z = 1.2 * calor_thickness

    # World
    external.World = {
        "WorldMaterial": default_material,
        "Type": "ExternalWorldCreator",
        "WorldSizeX": world_size_XY / 2,
        "WorldSizeY": world_size_XY / 2,
        "WorldSizeZ": world_size_Z / 2,
    }

    shapes = {}
    sensitive = {}
    hit = {}
    moni = {}

    # Calorimeter
    calor_name = f"{emb_name}_Calorimeter"
    calor_lvol_name = f"{calor_name}_lVol"

    shapes[calor_name] = {
        "Type": "Cuboid",
        "LogicalVolumeName": calor_lvol_name,
        "MaterialName": default_material,
        "xSize": calor_size_xy,
        "ySize": calor_size_xy,
        "zSize": calor_thickness,
        "xPos": 0.0,
        "yPos": 0.0,
        "zPos": 0.0,
    }

    # Layer
    layer_base_name = f"{emb_name}_Layer"
    layer_lvol_name = "Layer_lVol"
    layer_config = {
        "Type": "Cuboid",
        "MotherVolumeName": calor_lvol_name,
        "LogicalVolumeName": layer_lvol_name,
        "MaterialName": default_material,
        "xSize": calor_size_xy,
        "ySize": calor_size_xy,
        "zSize": layer_thickness,
        "xPos": 0.0,
        "yPos": 0.0,
    }

    # Position layers
    z_position = -calor_thickness / 2.0
    for i in range(n_layers):
        # Layer
        layer_name = f"{layer_base_name}_{i}"
        layer_position = z_position + (layer_thickness / 2.0)
        shapes[layer_name] = {
            **layer_config,
            "zPos": layer_position,
            "pCopyNo": i,
        }

        z_position += layer_thickness

    # Absorber
    absorber_name = f"{layer_base_name}_Absorber"
    shapes[absorber_name] = {
        "Type": "Cuboid",
        "MotherVolumeName": layer_lvol_name,
        "MaterialName": absorber_material,
        "xSize": calor_size_xy,
        "ySize": calor_size_xy,
        "zSize": absorber_thickness,
        "xPos": 0.0,
        "yPos": 0.0,
        "zPos": -gap_thickness / 2.0,
    }
    sensitive[absorber_name] = {
        "Type": "CalorimeterCollectorSensDet",
        "NofLayers": n_layers,
    }

    # Gap
    gap_name = f"{layer_base_name}_Gap"
    shapes[gap_name] = {
        "Type": "Cuboid",
        "MotherVolumeName": layer_lvol_name,
        "MaterialName": gap_material,
        "xSize": calor_size_xy,
        "ySize": calor_size_xy,
        "zSize": gap_thickness,
        "xPos": 0.0,
        "yPos": 0.0,
        "zPos": absorber_thickness / 2.0,
    }
    sensitive[gap_name] = {
        "Type": "CalorimeterCollectorSensDet",
        "NofLayers": n_layers,
    }

    external.Shapes = shapes
    external.Sensitive = sensitive
    external.Hit = hit
    external.Moni = moni

    external.Materials = {
        default_material: OUTER_SPACE,
        absorber_material: {
            "Type": "MaterialFromNIST",
        },
        gap_material: {
            "Type": "MaterialFromNIST",
        },
    }

    # Set Monitoring
    moni = CalorimeterMonitoring(
        "CalorimeterMonitoring",
        AbsorberCollectionName=f"{absorber_name}SDet/Hits",
        GapCollectionName=f"{gap_name}SDet/Hits",
        MaxGapEnergy=particle_energy * particles_per_event / units.GeV,
        MaxGapLength=calor_thickness * particles_per_event / units.m,
        MaxAbsorberEnergy=particle_energy * particles_per_event / units.GeV,
        MaxAbsorberLength=calor_thickness * particles_per_event / units.m,
    )

    ApplicationMgr().TopAlg.append(moni)


setup_geometry(
    emb_name="B4Calorimeter",
    n_layers=n_layers,
    calor_size_xy=calor_size_xy,
    absorber_thickness=absorber_thickness,
    gap_thickness=gap_thickness,
    default_material="OUTER_SPACE",
    gap_material="G4_Ar",
    absorber_material="G4_Pb",
)
