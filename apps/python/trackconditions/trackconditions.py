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

# Initialize empty dict in which all fetched Assetto Corsa data is stored
ac_data = {}
ac_data['wind_speed'] = 10

arrow = {}

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

    global ac_data
    global arrow

    global APP_HEIGHT, APP_ASPECT_RATIO

    #Update timers
    data_timer_60_hz += deltaT
    data_timer_0p1_hz += deltaT
    calc_timer_60_hz += deltaT
    
    PERIOD_60_HZ = 1 / 60
    PERIOD_0p1_HZ = 10

    # Retrieve data at 60 hz
    if data_timer_60_hz > PERIOD_60_HZ:
        # Reset timer
        data_timer_60_hz -= PERIOD_60_HZ

        # Wind direction is provided in degrees, 0 at north. Converted to radians.
        ac_data['wind_direction'] = ac.getWindDirection() * math.pi / 180
        # Car direction is provided in radians, 0 at south. Adjusted to 0 at north.
        ac_data['car_direction'] = info.physics.heading + math.pi

    # Retrieve data at 0.1 hz
    if data_timer_0p1_hz > PERIOD_0p1_HZ:
        # Reset timer
        data_timer_0p1_hz -= PERIOD_0p1_HZ

        # Get wind speed, air temp, road temp, track grip
        ac_data['wind_speed'] = ac.getWindSpeed()
        ac_data['air_temp'] = info.physics.airTemp
        ac_data['road_temp'] = info.physics.roadTemp 
        ac_data['track_grip'] = info.graphics.surfaceGrip

    # Calculations at 60 hz
    if calc_timer_60_hz > PERIOD_60_HZ:
        # Reset timer
        calc_timer_60_hz -= PERIOD_60_HZ

        # Calculations for wind arrow indicator
        # Calculate wind direction relative to car heading direction.
        arrow['angle'] = ac_data['wind_direction'] - ac_data['car_direction']

        arrow['origin'] = {'x': APP_HEIGHT * APP_ASPECT_RATIO - (APP_HEIGHT / 2), 'y': APP_HEIGHT / 2}
        arrow['radius'] = APP_HEIGHT * 0.4
        arrow['width'] = 0.5

        # If the wind speed is negligible (near 0), set angle to 0.
        if ac_data['wind_speed'] < 0.1:
            arrow['angle'] = 0

        # Calculate x,y coordinates to draw the four corners of the wind arrow
        arrow['xy_tip'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'], arrow['angle'])
        arrow['xy_bot_right'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'], arrow['angle'] + math.pi - arrow['width'])
        arrow['xy_bot_center'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'] * 0.5, arrow['angle'] + math.pi)
        arrow['xy_bot_left'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'], arrow['angle'] + math.pi + arrow['width'])

        # Arrow coloring from green (headwind) to yellow (sidewind) to red (tailwind).
        # arrow['angle'] can take on values between [-2pi, +2pi]
        # needs to be remapped from [-2pi, 0, 2pi] to [0, 1, 0] in a linear way
        arrow['color_shift'] = 1 - abs((abs(arrow['angle'])/math.pi - 1))

        if ac_data['wind_speed'] < 0.1:
            arrow['rgba'] = {'r': 0.6, 
                             'g': 0.6, 
                             'b': 0.6, 
                             'a': 0.6}
        else:
            if arrow['color_shift'] < 0.5:
                red_amount = 2 * arrow['color_shift']
                arrow['rgba'] = {'r': red_amount, 
                                 'g': 1, 
                                 'b': 0, 
                                 'a': 1}
            else:
                green_amount = 1 - (arrow['color_shift'] - 0.5) * 2
                arrow['rgba'] = {'r': 1, 
                                 'g': green_amount, 
                                 'b': 0, 
                                 'a': 1}


def onFormRender(deltaT):
    """Run every rendered frame of Assetto Corsa. """
    # Draw wind arrow indicator
    draw_wind_indicator()


def onFormRender_dev(deltaT):
    """Run every rendered frame of Assetto Corsa. """
    global label_wind_direction, label_car_direction, label_rel_direction
    global ac_wind_direction, ac_car_direction, ac_rel_direction

    ac.setText(label_wind_direction, "Wind Dir: {:.1f}".format(data_timer_0p1_hz))
    ac.setText(label_car_direction, "Car Dir: {:.2f}".format(ac_data['car_direction']))
    ac.setText(label_rel_direction, "Rel Dir: {:.2f}".format(arrow['angle']))


def draw_wind_indicator():
    """Draw wind indicator on app."""
    # Set wind indicator color
    ac.glColor4f(arrow['rgba']['r'], 
                 arrow['rgba']['g'], 
                 arrow['rgba']['b'], 
                 arrow['rgba']['a'])

    # Start drawing geometry. 3 stands for quad
    ac.glBegin(3)
    # Add vertices
    ac.glVertex2f(arrow['xy_tip']['x'], arrow['xy_tip']['y'])
    ac.glVertex2f(arrow['xy_bot_right']['x'], arrow['xy_bot_right']['y'])
    ac.glVertex2f(arrow['xy_bot_center']['x'], arrow['xy_bot_center']['y'])
    ac.glVertex2f(arrow['xy_bot_left']['x'], arrow['xy_bot_left']['y'])
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