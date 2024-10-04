from CaloChallenge.simulation import set_full_simulation
from CaloChallenge.geometry import planar_detector_SiW_options

set_full_simulation(planar_detector_SiW_options, "planar")

from Configurables import Gaussino

Gaussino().EvtMax = 10


#from Configurables import GiGaMTRunManagerFAC

#GiGaMTRunManagerFAC("GiGaMT.GiGaMTRunManagerFAC").InitCommands = [
#    "/process/eLoss/fluct false"
#]
