"""Simple example of a simulation with Gaussino"""

import os

from GaudiKernel import SystemOfUnits as units
from GaudiKernel import PhysicalConstants as constants
from Configurables import (
    Gaussino,
    GaussinoGeneration,
    GaussinoGeometry,
    ParticleGun,
    FixedMomentum,
    FlatSmearVertex,
    FlatNParticles,
    ExternalDetectorEmbedder,
)

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
n_chambers = 5
chamber_spacing = 80 * units.cm
chamber_width = 20 * units.cm

target_length = 5 * units.cm
target_radius = 0.5 * target_length

tracker_length = (n_chambers + 1) * chamber_spacing

world_length = 1.2 * (2 * target_length + tracker_length)


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
    # World
    world_material="G4_AIR",
    world_length=None,
    # Target
    target_material="G4_Pb",
    target_length=None,
    target_radius=None,
    # Tracker
    tracker_material="G4_AIR",
    tracker_length=None,
    # Chambers
    n_chambers=5,
    chamber_material="G4_Xe",
    chamber_spacing=None,
    chamber_width=None,
):
    GaussinoGeometry().ExternalDetectorEmbedder = emb_name
    external = ExternalDetectorEmbedder(emb_name)

    # World
    external.World = {
        "WorldMaterial": world_material,
        "Type": "ExternalWorldCreator",
        "WorldSizeX": world_length / 2,
        "WorldSizeY": world_length / 2,
        "WorldSizeZ": world_length / 2,
    }

    shapes = {}
    sensitive = {}
    hit = {}
    moni = {}

    # Target
    target_name = f"{emb_name}_Target"
    target_z_pos = -(target_length + tracker_length) * 0.5

    shapes[target_name] = {
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

    shapes[tracker_name] = {
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
    first_position = -0.5 * tracker_length + chamber_spacing
    first_length = tracker_length / 10
    last_length = tracker_length

    half_width = 0.5 * chamber_width
    rmax_first = 0.5 * first_length

    rmax_incr = 0.5 * (last_length - first_length) / (n_chambers - 1)

    for chamber_no in range(n_chambers):
        chamber_name = f"{emb_name}_Chamber_{chamber_no}"
        z_position = first_position + chamber_no * chamber_spacing
        rmax = rmax_first + chamber_no * rmax_incr

        shapes[chamber_name] = {
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

        sensitive[chamber_name] = {
            "Type": "SimpleCollectorSensDet",
        }

    external.Shapes = shapes
    external.Sensitive = sensitive
    external.Hit = hit
    external.Moni = moni

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


setup_geometry(
    emb_name="ExternalDetectorEmbedder",
    world_material="G4_AIR",
    world_length=world_length,
    target_material="G4_Pb",
    target_length=target_length,
    target_radius=target_radius,
    tracker_material="G4_AIR",
    tracker_length=tracker_length,
    n_chambers=n_chambers,
    chamber_material="G4_Pb",
    chamber_spacing=chamber_spacing,
    chamber_width=chamber_width,
)
