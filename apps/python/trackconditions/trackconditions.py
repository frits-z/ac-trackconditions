import ac
import acsys

import os
import sys
import platform
import math
import configparser

# Import Assetto Corsa shared memory library.
# Uses ctypes module, which is not included in AC python.
# Point to correct ctypes module based on platform architecture.
if platform.architecture()[0] == "64bit":
    sysdir = 'apps/python/trackconditions/dll/stdlib64'
else:
    sysdir = 'apps/python/trackconditions/dll/stdlib'

sys.path.insert(0, sysdir)
os.environ['PATH'] = os.environ['PATH'] + ";."

from trackconditions_lib.sim_info import info

# Initialize static variables.
APP_HEIGHT = 150
APP_ASPECT_RATIO = 2
BACKGROUND_OPACITY = 0.5


ac_wind_speed = 10

# Timers
data_timer_60_hz = 0
data_timer_0p1_hz = 8
calc_timer_60_hz = 0


def acMain(ac_version):
    """Run upon startup of Assetto Corsa. """
    global APP_HEIGHT, APP_ASPECT_RATIO
    global label_wind_direction, label_car_direction, label_rel_direction

    app_window = ac.newApp("Track Conditions")
    ac.setSize(app_window, (APP_ASPECT_RATIO * APP_HEIGHT), APP_HEIGHT)
    ac.setBackgroundOpacity(app_window, BACKGROUND_OPACITY)
    ac.setTitle(app_window, "")
    ac.setIconPosition(app_window, 0, -10000)
    ac.addRenderCallback(app_window, onFormRender)

    


    # Temporary code whilst developing the app
    dev_window = ac.newApp("TC Dev Mode")
    ac.setSize(dev_window, 300, 300)
    ac.setBackgroundOpacity(dev_window, 0.5)
    ac.setTitle(dev_window, "TC Dev Mode")
    ac.addRenderCallback(dev_window, onFormRender_dev)

    label_wind_direction = ac.addLabel(dev_window, "Wind Dir (deg)")
    ac.setPosition(label_wind_direction, 10, 20)
    ac.setFontSize(label_wind_direction, 24)

    label_car_direction = ac.addLabel(dev_window, "Car Dir (deg)")
    ac.setPosition(label_car_direction, 10, 60)
    ac.setFontSize(label_car_direction, 24)

    label_rel_direction = ac.addLabel(dev_window, "Rel Dir (deg)")
    ac.setPosition(label_rel_direction, 10, 100)
    ac.setFontSize(label_rel_direction, 24)


def acUpdate(deltaT):
    """Run every physics tick of Assetto Corsa. """
    global data_timer_60_hz, data_timer_0p1_hz
    global calc_timer_60_hz
    global ac_rel_direction, ac_car_direction, ac_wind_direction, ac_wind_speed
    global APP_HEIGHT, APP_ASPECT_RATIO
    global color_shift_percent
    global arrow_coords

    #Update timers
    data_timer_60_hz += deltaT
    data_timer_0p1_hz += deltaT
    calc_timer_60_hz += deltaT
    
    PERIOD_60_HZ = 1 / 60
    PERIOD_0p1_HZ = 10

    # Retrieve data
    if data_timer_60_hz > PERIOD_60_HZ:
        # Reset timer
        data_timer_60_hz -= PERIOD_60_HZ

        # Wind direction supplied in degrees, 0 at north. Converted to radians.
        ac_wind_direction = ac.getWindDirection() * math.pi / 180
        # Car direction supplied in radians, 0 at south. Adjusted to 0 at north.
        ac_car_direction = info.physics.heading + math.pi

    if data_timer_0p1_hz > PERIOD_0p1_HZ:
        # Reset timer
        data_timer_0p1_hz -= PERIOD_0p1_HZ
        # Get wind speed, air temp, road temp, track grip
        ac_wind_speed = ac.getWindSpeed()
        ac_air_temp = info.physics.airTemp
        ac_road_temp = info.physics.roadTemp 
        ac_track_grip = info.graphics.surfaceGrip

    # Calculations
    if calc_timer_60_hz > PERIOD_60_HZ:
        # Reset timer
        calc_timer_60_hz -= PERIOD_60_HZ

        # Calculate wind direction relative to car heading direction.
        ac_rel_direction = ac_wind_direction - ac_car_direction

        arrow_origin = {'x': APP_HEIGHT * APP_ASPECT_RATIO - (APP_HEIGHT / 2), 'y': APP_HEIGHT / 2}
        arrow_radius = APP_HEIGHT * 0.4
        ARROW_WIDTH = 0.5

        if ac_wind_speed < 0.1:
            ac_rel_direction = 0

        # Tip of the arrow
        arrow_u = polar_to_cartesian_coords(arrow_origin, arrow_radius, ac_rel_direction)
        # Right point of the arrow
        arrow_r = polar_to_cartesian_coords(arrow_origin, arrow_radius, ac_rel_direction + math.pi - ARROW_WIDTH)
        # Bottom point of the arrow
        arrow_d = polar_to_cartesian_coords(arrow_origin, arrow_radius * 0.5, ac_rel_direction + math.pi)
        # Left point of the arrow
        arrow_l = polar_to_cartesian_coords(arrow_origin, arrow_radius, ac_rel_direction + math.pi + ARROW_WIDTH)
        # Turn coordinates into a list to avoid using many arguments
        arrow_coords = [arrow_u, arrow_r, arrow_d, arrow_l]

        # ac_rel_direction can range fron -2pi to +2pi.
        # needs to be remapped from [-2pi, 0, 2pi] to [0, 1, 0]
        color_shift_percent = 1 - abs((abs(ac_rel_direction)/math.pi - 1))


def onFormRender(deltaT):
    """Run every rendered frame of Assetto Corsa. """
    global ac_rel_direction, ac_wind_speed

    draw_wind_indicator(arrow_coords, ac_wind_speed)


def onFormRender_dev(deltaT):
    """Run every rendered frame of Assetto Corsa. """
    global label_wind_direction, label_car_direction, label_rel_direction
    global ac_wind_direction, ac_car_direction, ac_rel_direction

    ac.setText(label_wind_direction, "Wind Dir: {:.1f}".format(data_timer_0p1_hz))
    ac.setText(label_car_direction, "Car Dir: {:.2f}".format(ac_car_direction))
    ac.setText(label_rel_direction, "Rel Dir: {:.2f}".format(ac_rel_direction))


def draw_wind_indicator(arrow_coords, ac_wind_speed):
    """Draw wind indicator on app

    Args:
        ac_rel_direction (float): Wind direction relative to car heading direction in radians.
        ac_wind_speed (float): Wind speed in in kmh
    """
    if ac_wind_speed < 0.1:
        ac.glColor4f(0.6, 0.6, 0.6, 0.6)
    else:
        if color_shift_percent < 0.5:
            red_amount = 2 * color_shift_percent
            ac.glColor4f(red_amount, 1, 0, 1)
        else:
            green_amount = 1 - (color_shift_percent - 0.5) * 2
            ac.glColor4f(1, green_amount, 0, 1)

    ac.glBegin(3)
    # Add points
    for vertex in arrow_coords:
        ac.glVertex2f(vertex['x'], vertex['y'])
    ac.glEnd()


def polar_to_cartesian_coords(origin, radius, phi):
    """Convert polar coordinate system to cartesian coordinate system around specified origin.

    Args:
        origin (dict): x,y origin cartesian coordinates.
        radius (float): length of the point to the origin.
        phi (float): Radians rotation (relative to north).

    Returns:
        dict: cartesian x,y coordinates.
    """
    # Add half-pi offset on phi because it takes the x-axis as a zero point.
    # This would be east for the wind directions application. Need to have north as zero point.
    phi -= 0.5 * math.pi
    cartesian_x = radius * math.cos(phi) + origin['x']
    cartesian_y = radius * math.sin(phi) + origin['y']
    return {'x': cartesian_x, 'y': cartesian_y}