import os

from Configurables import Gaussino

from CaloChallenge.cc_simulation import set_full_simulation
from CaloChallenge.cc_geometry import planar_detector_SiW_options

set_full_simulation(planar_detector_SiW_options, "planar")


particles_per_event = int(os.environ.get("PARTICLES_PER_EVENT", 100))

Gaussino().EvtMax = 10
