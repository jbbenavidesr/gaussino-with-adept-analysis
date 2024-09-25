from GaudiKernel import SystemOfUnits as units
from Configurables import Gaussino

Gaussino().EvtMax = 5
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
pgun.FlatNParticles.MinNParticles = 1
pgun.FlatNParticles.MaxNParticles = 1
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
