import os

from Configurables import GaussinoSimulation, GiGaMTRunManagerFAC
from Configurables import Gaussino

from GaudiKernel import SystemOfUnits as units
from Gaudi.Configuration import appendPostConfigAction

from CaloChallenge.cc_geometry import planar_detector_SiW_options


number_of_events = int(os.environ.get("NUMBER_OF_EVENTS", 10))

Gaussino().EvtMax = number_of_events
Gaussino().ConvertEDM = True

GaussinoSimulation(
    PhysicsConstructors=[
        "GiGaMT_G4EmStandardPhysics_option2_AdePT",
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

GiGaMTRunManagerFAC("GiGaMT.GiGaMTRunManagerFAC").InitCommands = [
    "/adept/verbose 4",
    "/adept/setCUDAStackLimit 8192",
    # "/adept/CallUserTrackingAction true",
    # "/adept/addGPURegion CaloRegion",
    "/adept/setTrackInAllRegions true",
    "/adept/setMillionsOfTrackSlots 7",
    "/adept/setMillionsOfHitSlots 24",
]


def updateStoreMax():
    from Configurables import TruthFlaggingTrackAction

    trth = TruthFlaggingTrackAction(
        "GiGaMT.GiGaActionInitializer.TruthFlaggingTrackAction"
    )
    trth.StoreUpToRho = False
    trth.StoreUpToZ = True
    trth.ZmaxForStoring = planar_detector_SiW_options["detector_z_pos"]
    # optimization for the training dataset
    # make sure you only have one collector hit per particle
    trth.StorePrimaries = True
    trth.StoreByOwnEnergy = True
    trth.OwnEnergyThreshold = 0.1 * units.GeV
    trth.StoreAll = False
    trth.StoreForcedDecays = False
    trth.StoreByOwnProcess = False
    trth.StoreByOwnType = False
    trth.StoreByChildProcess = False
    trth.StoreByChildEnergy = False
    trth.StoreByChildType = False


appendPostConfigAction(updateStoreMax)


from Gaudi.Configuration import appendPostConfigAction


def after():
    from Configurables import (
        CustomSimulationRegionFactory,
        GiGaMTDetectorConstructionFAC,
    )

    dettool = GiGaMTDetectorConstructionFAC("GiGaMT.DetConst")
    region_factory = CustomSimulationRegionFactory(
        Name="CaloRegion",
        Volumes=["DetectorLVol"],
    )
    dettool.addTool(region_factory, name="CaloRegion")
    dettool.CustomSimulationRegionFactories.append(getattr(dettool, "CaloRegion"))


appendPostConfigAction(after)
