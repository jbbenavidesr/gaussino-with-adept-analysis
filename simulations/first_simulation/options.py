import os
from GaudiKernel import SystemOfUnits as units
from Configurables import Gaussino


evt_max = os.environ.get("EVT_MAX", 1)
particles_per_event = os.environ.get("PARTICLES_PER_EVENT", 1)

print(f"{evt_max=}, {particles_per_event=}")

Gaussino().EvtMax = evt_max
Gaussino().Phases = ["Generator", "Simulation"]


# Generation
from Configurables import (
    GaussinoGeneration,
    ParticleGun,
    FixedMomentum,
    FlatNParticles,
)

GaussinoGeneration().ParticleGun = True
pgun = ParticleGun("ParticleGun")
pgun.addTool(FixedMomentum, name="FixedMomentum")
pgun.ParticleGunTool = "FixedMomentum"
pgun.addTool(FlatNParticles, name="FlatNParticles")
pgun.NumberOfParticlesTool = "FlatNParticles"
pgun.FlatNParticles.MinNParticles = particles_per_event 
pgun.FlatNParticles.MaxNParticles = particles_per_event 
pgun.FixedMomentum.px = 0.0 * units.GeV
pgun.FixedMomentum.py = 0.0 * units.GeV
pgun.FixedMomentum.pz = 1.0 * units.GeV
pgun.FixedMomentum.PdgCodes = [22]


# Simulation
from Configurables import GaussinoSimulation

GaussinoSimulation().PhysicsConstructors.append("GiGaMT_G4EmStandardPhysics")

# Geometry
from Configurables import (
    GaussinoGeometry,
    ExternalDetectorEmbedder,
)
from ExternalDetector.Materials import (
    OUTER_SPACE,
    LEAD,
)

emb_name = "ExternalDetectorEmbedder_0"
cube_name = f"{emb_name}_Cube"

GaussinoGeometry().ExternalDetectorEmbedder = emb_name
external = ExternalDetectorEmbedder(emb_name)
external.Shapes = {
    cube_name: {
        "Type": "Cuboid",
        "xSize": 1.0 * units.m,
        "ySize": 1.0 * units.m,
        "zSize": 1.0 * units.m,
        "MaterialName": "Pb",
    },
}

external.Sensitive = {
    cube_name: {
        "Type": "MCCollectorSensDet",
    },
}

external.World = {
    "WorldMaterial": "OuterSpace",
    "Type": "ExternalWorldCreator",
}


external.Materials = {
    # material needed for the external world
    "OuterSpace": OUTER_SPACE,
    # material needed for the lead cube
    "Pb": LEAD,
}
