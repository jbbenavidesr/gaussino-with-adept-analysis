from Configurables import GaussinoSimulation, GiGaMTRunManagerFAC, GiGaMTDetectorConstructionFAC
from GaudiKernel import SystemOfUnits as units
import Configurables

from Configurables import Gaussino

Gaussino().EvtMax = 10

GaussinoSimulation(
    PhysicsConstructors=[
        "GiGaMT_AdePTPhysics",
        "GiGaMT_G4EmStandardPhysics",
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
    "/adept/setVecGeomGDML calochallenge.gdml",
    "/adept/setCUDAStackLimit 4096",
    "/adept/addGPURegion CaloRegion", #"/adept/setTrackInAllRegions true"
]

from Gaudi.Configuration import appendPostConfigAction
from CaloChallenge.geometry import planar_detector_SiW_options

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
    dettool.CustomSimulationRegionFactories.append(
        getattr(dettool, "CaloRegion")
    )
appendPostConfigAction(after)
