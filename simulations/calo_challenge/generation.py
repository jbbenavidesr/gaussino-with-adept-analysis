from CaloChallenge.geometry import planar_detector_SiW_options
from CaloChallenge.generation import set_particle_gun, set_particle_gun_momentum_range

from GaudiKernel import SystemOfUnits as units
from GaudiKernel import PhysicalConstants as constants


set_particle_gun(planar_detector_SiW_options, "MomentumRange", "planar", pdg_codes = [22])


set_particle_gun_momentum_range(
    min_particles_no=1000,
    max_particles_no=1000,
    pdg_codes=[22],
    min_momentum=1.0 * units.GeV,
    max_momentum=1.0 * units.GeV,
    theta_min=0,
    theta_max=constants.pi,
)

# Fix for truth tracking

from Configurables import GiGaMT
GiGaMT().HepMCConverter.CheckParticle = False
