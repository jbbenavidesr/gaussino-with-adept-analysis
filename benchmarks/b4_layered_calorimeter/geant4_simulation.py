import os
from Configurables import Gaussino
from SamplingCalorimeter.calorimeter_simulation import set_full_simulation

# Configure standard Geant4 simulation
set_full_simulation()

# General Gaussino configuration
Gaussino().EvtMax = int(os.environ.get("NUMBER_OF_EVENTS", 10))
Gaussino().Phases = ["Generator", "Simulation"]
Gaussino().EnableHive = True
Gaussino().ThreadPoolSize = int(os.environ.get("NUMBER_OF_THREADS", 1))
Gaussino().EventSlots = int(os.environ.get("NUMBER_OF_THREADS", 1))
