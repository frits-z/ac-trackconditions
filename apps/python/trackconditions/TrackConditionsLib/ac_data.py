import ac
import acsys
import os
import sys
import platform
import math

# Import Assetto Corsa shared memory library.
# It has a dependency on ctypes, which is not included in AC python version.
# Point to correct ctypes module based on platform architecture.
# First, get directory of the app, then add correct folder to sys.path.
app_dir = os.path.dirname(os.path.dirname(__file__))

if platform.architecture()[0] == "64bit":
    sysdir = os.path.join(app_dir, 'dll', 'stdlib64')
else:
    sysdir = os.path.join(app_dir, 'dll', 'stdlib')
# Python looks in sys.path for modules to load, insert new dir first in line.
sys.path.insert(0, sysdir)
os.environ['PATH'] = os.environ['PATH'] + ";."

from TrackConditionsLib.sim_info import info

class Session:
    """Handling all data from AC that is not car-specific.
    
    Args:
        cfg (obj:Config): App configuration.
    """
    def __init__(self, cfg):
        # Config object
        self.cfg = cfg

        # Initialize session data attributes
        self.focused_car_id = 0
        # Status of the instance (0: OFF, 1: REPLAY, 2: LIVE, 3: PAUSE)
        self.status = 0

        # Main data items
        self.wind_dir = 0
        self.wind_speed = 0
        self.air_temp = 0
        self.road_temp = 0
        self.track_grip = 0

        # TODO add session type... To find out replay or not etc.

        # Initialize focused car object
        self.focused_car = Car(cfg, self.focused_car_id)

    def update(self):
        """Update session data."""
        # Update session attributes first, then car specific ones.
        self.focused_car_id = ac.getFocusedCar()
        self.status = info.graphics.status

        # Wind direction is provided in degrees, 0 at north. Converted to radians.
        self.wind_dir = ac.getWindDirection() * math.pi / 180
        self.wind_speed = ac.getWindSpeed()
        self.air_temp = info.physics.airTemp
        self.road_temp = info.physics.roadTemp
        self.track_grip = info.graphics.surfaceGrip * 100

        # Update car
        self.focused_car.set_id(self.focused_car_id)
        self.focused_car.update()


class Car:
    """Handling all data from AC that is car-specific.
    
    Args:
        cfg (obj:Config): App configuration.
        car_id (int, optional): Car ID number to retrieve data from.
            Defaults to own car.
    """
    def __init__(self, cfg, car_id=0):
        self.cfg = cfg
        self.id = car_id

        # Initialize car data attributes
        self.heading_dir = 0


    def set_id(self, car_id):
        """Update car ID to retrieve data from.
        
        Args:
            car_id (int): Car ID number."""
        self.id = car_id

    def update(self):
        """Update data."""

        # Car direction is provided in radians, 0 at south. Adjusted to 0 at north.
        self.heading_dir = info.physics.heading + math.pi