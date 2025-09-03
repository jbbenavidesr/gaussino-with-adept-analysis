from Configurables import (
    GaussinoSimulation,
    GiGaMTRunManagerFAC,
)

GaussinoSimulation(
    PhysicsConstructors=[
        "GiGaMT_G4EmStandardPhysics_option2_HepEm",
        "GiGaMT_G4EmExtraPhysics",
        "GiGaMT_G4DecayPhysics",
        "GiGaMT_G4HadronElasticPhysics",
        "GiGaMT_G4HadronPhysicsFTFP_BERT",
        "GiGaMT_G4StoppingPhysics",
        "GiGaMT_G4IonPhysics",
        "GiGaMT_G4NeutronTrackingCut",
    ],
)

GiGaMTRunManagerFAC("GiGaMT.GiGaMTRunManagerFAC").InitCommands = [
    "/adept/verbose 4",
    "/adept/setCUDAStackLimit 8192",
    "/adept/CallUserTrackingAction true",
    "/adept/CallUserSteppingAction true",
    "/adept/setTrackInAllRegions true",
    "/adept/setMillionsOfTrackSlots 14",
    "/adept/setMillionsOfHitSlots 24",
]
