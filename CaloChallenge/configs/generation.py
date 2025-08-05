import os

from Configurables import GiGaMT

from CaloChallenge.cc_geometry import planar_detector_SiW_options
from CaloChallenge.cc_generation import (
    set_particle_gun,
    set_particle_gun_momentum_range,
)

from GaudiKernel import SystemOfUnits as units
from GaudiKernel import PhysicalConstants as constants


particle_types = {
    "proton": 2212,
    "electron": 11,
    "gamma": 22,
}


particle_type = particle_types.get(os.environ.get("PARTICLE_TYPE", "gamma"), 22)
particles_per_event = int(os.environ.get("PARTICLES_PER_EVENT", 100))

set_particle_gun(
    planar_detector_SiW_options, "MomentumRange", "planar", pdg_codes=[particle_type]
)


set_particle_gun_momentum_range(
    min_particles_no=particles_per_event,
    max_particles_no=particles_per_event,
    pdg_codes=[particle_type],
    min_momentum=1.0 * units.GeV,
    max_momentum=1.0 * units.GeV,
    theta_min=0,
    theta_max=constants.pi,
)

# Fix for truth tracking

GiGaMT().HepMCConverter.CheckParticle = False
