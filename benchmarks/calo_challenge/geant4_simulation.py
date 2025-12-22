import os

from Configurables import Gaussino

from CaloChallenge.cc_simulation import set_full_simulation
from CaloChallenge.cc_geometry import planar_detector_SiW_options

set_full_simulation(planar_detector_SiW_options, "planar")


number_of_events = int(os.environ.get("NUMBER_OF_EVENTS", 10))
nthreads = int(os.environ.get("NUMBER_OF_THREADS", 1))

Gaussino().EvtMax = number_of_events
Gaussino().ConvertEDM = True
Gaussino().EnableHive = True
Gaussino().ThreadPoolSize = nthreads
Gaussino().EventSlots = nthreads
