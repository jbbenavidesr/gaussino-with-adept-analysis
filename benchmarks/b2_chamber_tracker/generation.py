import os
from GaudiKernel import SystemOfUnits as units
from TargetTracker.tracker_geometry import tracker_default_options
from TargetTracker.tracker_generation import set_particle_gun

# Particle type mapping
particle_types = {
    "proton": 2212,
    "electron": 11,
    "gamma": 22,
}

# Read parameters from environment variables
particle_type = particle_types.get(os.environ.get("PARTICLE_TYPE", "electron"), 11)
particles_per_event = int(os.environ.get("PARTICLES_PER_EVENT", 100))
particle_energy = float(os.environ.get("PARTICLE_ENERGY_MEV", 10.0)) * units.MeV

# Configure particle gun
set_particle_gun(
    geometry_opts=tracker_default_options,
    particle_type=particle_type,
    particle_energy=particle_energy,
    particles_per_event=particles_per_event,
)
