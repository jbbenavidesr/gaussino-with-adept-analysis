from Configurables import GaussinoSimulation

from GaudiKernel import SystemOfUnits as units

GaussinoSimulation(
    PhysicsConstructors=[
        "GiGaMT_G4EmStandardPhysics_option2",
        "GiGaMT_G4EmExtraPhysics",
        "GiGaMT_G4DecayPhysics",
        "GiGaMT_G4HadronElasticPhysics",
        "GiGaMT_G4HadronPhysicsFTFP_BERT",
        "GiGaMT_G4StoppingPhysics",
        "GiGaMT_G4IonPhysics",
        "GiGaMT_G4NeutronTrackingCut",
    ],
    CutForElectron=700 * units.micrometer,
    CutForPositron=700 * units.micrometer,
    CutForGamma=700 * units.micrometer,
    DumpCutsTable=True,
)
