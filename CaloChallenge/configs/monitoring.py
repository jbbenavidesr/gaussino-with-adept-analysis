from GaudiKernel import SystemOfUnits as units

from CaloChallenge.cc_monitoring import set_monitoring
from CaloChallenge.cc_geometry import planar_detector_SiW_options

set_monitoring(
    planar_detector_SiW_options,
    max_energy_hist=100 * units.GeV,
    training_data=False,
)
