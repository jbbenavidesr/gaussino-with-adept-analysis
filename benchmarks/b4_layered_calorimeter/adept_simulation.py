import os
from Configurables import Gaussino
from SamplingCalorimeter.calorimeter_simulation import set_adept_simulation

# Read AdePT configuration from environment
adept_verbosity = int(os.environ.get("ADEPT_VERBOSITY", 0))
track_slots = int(os.environ.get("ADEPT_TRACK_SLOTS", 14))
hit_slots = int(os.environ.get("ADEPT_HIT_SLOTS", 40))
use_adept = os.environ.get("USE_ADEPT", "true").lower() == "true"

# Configure AdePT or G4HepEm simulation
set_adept_simulation(
    adept_verbosity=adept_verbosity,
    track_slots=track_slots,
    hit_slots=hit_slots,
    use_adept=use_adept,
)

# General Gaussino configuration
Gaussino().EvtMax = int(os.environ.get("NUMBER_OF_EVENTS", 10))
Gaussino().Phases = ["Generator", "Simulation"]
Gaussino().EnableHive = True
Gaussino().ThreadPoolSize = int(os.environ.get("NUMBER_OF_THREADS", 1))
Gaussino().EventSlots = int(os.environ.get("NUMBER_OF_THREADS", 1))
