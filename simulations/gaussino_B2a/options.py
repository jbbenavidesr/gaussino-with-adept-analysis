"""Simple example of a simulation with Gaussino"""
from GaudiKernel import SystemOfUnits as units
from GaudiKernel import PhysicalConstants as constants
from Configurables import (
    Gaussino,
    GaussinoGeneration,
    GaussinoSimulation,
    GaussinoGeometry,
    ParticleGun,
    FixedMomentum,
    FlatSmearVertex,
    FlatNParticles,
    ExternalDetectorEmbedder,
    GiGaMTRunManagerFAC,
)

## constants
nthreads = 1

n_chambers = 5
chamber_spacing = 80 * units.cm
chamber_width = 20 * units.cm

target_length = 5 * units.cm
target_radius = 0.5 * target_length

tracker_length = (n_chambers + 1) * chamber_spacing

world_length = 1.2 * ( 2 * target_length + tracker_length)



# General Gaussino configs
Gaussino().EvtMax = 10
Gaussino().Phases = ["Generator", "Simulation"]
Gaussino().EnableHive = True
Gaussino().ThreadPoolSize = nthreads
Gaussino().EventSlots = nthreads

# Setup the generation phase by defining a Particle Gun
GaussinoGeneration().ParticleGun = True
pgun = ParticleGun("ParticleGun")
pgun.addTool(FixedMomentum, name="FixedMomentum")
pgun.ParticleGunTool = "FixedMomentum"
pgun.addTool(FlatNParticles, name="FlatNParticles")
pgun.NumberOfParticlesTool = "FlatNParticles"
pgun.FlatNParticles.MinNParticles = 1
pgun.FlatNParticles.MaxNParticles = 1
pgun.FixedMomentum.px = 0.0 * units.GeV
pgun.FixedMomentum.py = 0.0 * units.GeV
pgun.FixedMomentum.pz = 3.0 * units.GeV
pgun.FixedMomentum.PdgCodes = [22]

pgun.addTool(FlatSmearVertex, name="FlatSmearVertex")
pgun.FlatSmearVertex.xVertexMin = 0.0 * units.mm
pgun.FlatSmearVertex.xVertexMax = 0.0 * units.mm
pgun.FlatSmearVertex.yVertexMin = 0.0 * units.mm
pgun.FlatSmearVertex.yVertexMax = 0.0 * units.mm
pgun.FlatSmearVertex.zVertexMin = -0.5 * world_length 
pgun.FlatSmearVertex.zVertexMax = -0.5 * world_length

# Sets up the simulation phase.
# Here you define the physics lists and would include AdePT
GaussinoSimulation().PhysicsConstructors.append("GiGaMT_G4EmStandardPhysics")
GaussinoSimulation().PhysicsConstructors.append("GiGaMT_AdePTPhysics")

GiGaMTRunManagerFAC("GiGaMT.GiGaMTRunManagerFAC").InitCommands = [
    "/adept/setVecGeomGDML export.gdml",
    "/adept/setTrackInAllRegions true",
    "/adept/setCUDAStackLimit 4096",
]

########################
#    Setup Geometry    # 
########################
emb_name = "ExternalDetectorEmbedder"
GaussinoGeometry().ExternalDetectorEmbedder = emb_name
external = ExternalDetectorEmbedder(emb_name)

# World
world_material = "G4_AIR"
external.World = {
    "WorldMaterial": world_material,
    "Type": "ExternalWorldCreator",
    "WorldSizeX": world_length / 2,
    "WorldSizeY": world_length / 2,
    "WorldSizeZ": world_length / 2,

}

# Target
target_name = f"{emb_name}_Target"
target_z_pos = - (target_length + tracker_length) * 0.5
target_material = "G4_WATER"

external.Shapes[target_name] = {
    "Type": "Tube",
    "MaterialName": target_material,
    "RMin": 0,
    "RMax": target_radius,
    "Dz": target_length / 2.0,
    "SPhi": 0,
    "DPhi": 2 * constants.pi * units.radian,
    "zPos": target_z_pos,
}

# Tracker
tracker_name = f"{emb_name}_Tracker"
tracker_lvol_name = f"{tracker_name}_lVol"
tracker_material = "G4_AIR"

external.Shapes[tracker_name] = {
    "Type": "Tube",
    "LogicalVolumeName": tracker_lvol_name,
    "MaterialName": tracker_material,
    "RMin": 0,
    "RMax": tracker_length / 2.0,
    "Dz": tracker_length / 2.0,
    "SPhi": 0,
    "DPhi": 2 * constants.pi * units.radian,
}

# Chambers
chamber_material = "G4_Pb"
first_position = - 0.5 * tracker_length + chamber_spacing
first_length = tracker_length / 10
last_length = tracker_length

half_width = 0.5 * chamber_width
rmax_first = 0.5 * first_length

rmax_incr = 0.5 * (last_length - first_length) / (n_chambers - 1)

for chamber_no in range(n_chambers):
    chamber_name = f"{emb_name}_Chamber_{chamber_no}"
    z_position = first_position + chamber_no * chamber_spacing
    rmax = rmax_first + chamber_no * rmax_incr

    external.Shapes[chamber_name] = {
        "Type": "Tube",
        "MaterialName": chamber_material,
        "RMin": 0,
        "RMax": rmax,
        "Dz": half_width,
        "SPhi": 0,
        "DPhi": 2 * constants.pi * units.radian,
        "zPos": z_position,
        "MotherVolumeName": tracker_lvol_name,
    }

    # Make Chamber Sensitive
    external.Sensitive[chamber_name] = {
        "Type": "MCCollectorSensDet",
    }



external.Materials = {
    world_material: {
        "Type": "MaterialFromNIST",
    },
    target_material: {
        "Type": "MaterialFromNIST",
    },
    tracker_material: {
        "Type": "MaterialFromNIST",
    },
    chamber_material: {
        "Type": "MaterialFromNIST",
    },
}

# GaussinoGeometry().ExportGDML = {
#     "GDMLFileName": "export.gdml",
#     # G4 will crash if the file with same name already exists
#     "GDMLFileNameOverwrite": True,
#     # add unique references to the names
#     "GDMLAddReferences": True,
#     # export auxilliary information
#     "GDMLExportEnergyCuts": True,
#     "GDMLExportSD": True,
# }
