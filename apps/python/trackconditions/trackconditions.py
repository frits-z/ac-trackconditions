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

# Start configparser
config = configparser.ConfigParser()
configfile = "apps/python/trackconditions/config.ini"
config.read(configfile)

# Initialize app_info, dict in which basic app info is stored.
app_info = {}
app_info['name'] = "Track Conditions"

try:
    app_info['height'] = config.getint('GENERAL', 'app_height')
except Exception as error:
    app_info['height'] = 150
    ac.log("{}: app_height Error: {}".format(app_info['name'], str(error)))

app_info['aspect_ratio'] = 2.25
app_info['title'] = "" 
app_info['padding'] = 0.1
app_info['width'] = app_info['height'] * app_info['aspect_ratio']

# Initialize empty dict in which the text labels are stored.
labels = {}

# Initialize empty dict in which fetched Assetto Corsa data is stored.
ac_data = {}
ac_data['wind_speed'] = 10
ac_data['track_grip'] = 0
ac_data['road_temp'] = 0
ac_data['air_temp'] = 0

# Initialize empty dict in which wind arrow indicator data is stored.
arrow = {}

# Timers
data_timer_60_hz = 0
data_timer_0p1_hz = 8
calc_timer_60_hz = 0

def acMain(ac_version):
    """Run upon startup of Assetto Corsa. """
    global app_info, app_window
    global labels

    # Initialize app window
    app_window = ac.newApp(app_info['name'])
    ac.setSize(
            app_window, 
            app_info['width'], 
            app_info['height']
        )
    background = "apps/python/trackconditions/img/bg.png"
    ac.setBackgroundTexture(app_window, background)
    ac.setBackgroundOpacity(app_window, 0)
    ac.drawBorder(app_window, 0)
    ac.setTitle(app_window, app_info['title'])
    ac.setIconPosition(app_window, 0, -10000)

    # run onFormRender every render call
    ac.addRenderCallback(app_window, onFormRender)

    # Initialize custom font
    ac.initFont(0, "Roboto Light", 0, 0)
    # Calculate fontsize based on padding and app height
    fontsize = (app_info['height'] * (1 - (2 + 3 * 0.5) * app_info['padding'])) / 4

    # Start the left-aligned text labels
    labels['grip_text'] = ac.addLabel(app_window, "GRIP:")
    labels['wind_text'] = ac.addLabel(app_window, "WIND:")
    labels['road_text'] = ac.addLabel(app_window, "ROAD:")
    labels['air_text'] = ac.addLabel(app_window, "AIR:")

    # Apply positioning, color, font, size and alignment to all data labels
    text_labels_list = ['grip_text', 'wind_text', 'road_text', 'air_text']
    for n, key in enumerate(text_labels_list):
        ac.setPosition(
            labels[key],
            app_info['padding'] * app_info['height'],
            (n - 0.35) * fontsize + (1 + 0.6 * n) * app_info['padding'] * app_info['height'])
        ac.setFontSize(labels[key], fontsize)
        ac.setCustomFont(labels[key], "Roboto Light", 0, 0)
        ac.setFontColor(labels[key], 0.9, 0.9, 0.9, 1)

    # Start right-aligned data labels
    labels['grip_data'] = ac.addLabel(app_window, "X%")
    labels['wind_data'] = ac.addLabel(app_window, "Xkmh")
    labels['road_data'] = ac.addLabel(app_window, "XC")
    labels['air_data'] = ac.addLabel(app_window, "XC")

    # Apply positioning, color, font, size and alignment to all data labels
    data_labels_list = ['grip_data', 'wind_data', 'road_data', 'air_data']
    for n, key in enumerate(data_labels_list):
        ac.setPosition(
            labels[key],
            app_info['height'] * (app_info['aspect_ratio'] - 1 - app_info['padding']),
            (n - 0.35) * fontsize + (1 + 0.6 * n) * app_info['padding'] * app_info['height'])
        ac.setFontSize(labels[key], fontsize)
        ac.setCustomFont(labels[key], "Roboto Light", 0, 0)
        ac.setFontColor(labels[key], 0.9, 0.9, 0.9, 1)
        ac.setFontAlignment(labels[key], "right")


def acUpdate(deltaT):
    """Run every physics tick of Assetto Corsa. """
    global app_info
    global ac_data
    global arrow

    global data_timer_60_hz, data_timer_0p1_hz
    global calc_timer_60_hz

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
        ac_data['track_grip'] = info.graphics.surfaceGrip * 100

    # Calculations at 60 hz
    if calc_timer_60_hz > PERIOD_60_HZ:
        # Reset timer
        calc_timer_60_hz -= PERIOD_60_HZ

        # Calculations for wind arrow indicator
        # Calculate wind direction relative to car heading direction.
        arrow['angle'] = ac_data['wind_direction'] - ac_data['car_direction']

        arrow['origin'] = {'x': app_info['height'] 
                                * app_info['aspect_ratio'] 
                                - (app_info['height'] / 2), 
                           'y': app_info['height'] / 2}
        arrow['radius'] = app_info['height'] * (0.5 - app_info['padding'])
        arrow['width'] = 0.5

        # If the wind speed is negligible (near 0), set angle to 0.
        if ac_data['wind_speed'] < 0.1:
            arrow['angle'] = 0

        # Calculate x,y coordinates to draw the four corners of the wind arrow
        arrow['xy_tip'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'], arrow['angle'])
        arrow['xy_bot_right'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'], arrow['angle'] + math.pi - arrow['width'])
        arrow['xy_bot_center'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'] * 0.5, arrow['angle'] + math.pi)
        arrow['xy_bot_left'] = polar_to_cartesian_coords(arrow['origin'], arrow['radius'], arrow['angle'] + math.pi + arrow['width'])

        # Arrow coloring
        if ac_data['wind_speed'] < 0.1:
            # With no (neglible) wind, make arrow grey.
            arrow['rgba'] = {'r': 0.6, 
                             'g': 0.6, 
                             'b': 0.6, 
                             'a': 0.6}
        else:
            # Arrow coloring from green (headwind) to yellow (sidewind) to red (tailwind).
            # arrow['angle'] can take on values between [-2pi, +2pi]
            # needs to be remapped from [-2pi, 0, 2pi] to [0, 1, 0] in a linear way
            arrow['color_shift'] = 1 - abs((abs(arrow['angle'])/math.pi - 1))

            if arrow['color_shift'] < 0.5:
                # From north to east/west shift color from green to yellow.
                red_amount = 2 * arrow['color_shift']
                arrow['rgba'] = {'r': red_amount, 
                                 'g': 1, 
                                 'b': 0, 
                                 'a': 1}
            else:
                # From east/west to south shift color from yellow to red.
                green_amount = 1 - (arrow['color_shift'] - 0.5) * 2
                arrow['rgba'] = {'r': 1, 
                                 'g': green_amount, 
                                 'b': 0, 
                                 'a': 1}


def onFormRender(deltaT):
    """Run every rendered frame of Assetto Corsa. """
    # When the user moves the window, the opacity is reset to default.
    # Therefore, opacity needs to be set to 0 every frame.
    ac.setBackgroundOpacity(app_window, 0)

    # Update text data lables
    ac.setText(labels['grip_data'], "{:.1f}%".format(ac_data['track_grip']))
    ac.setText(labels['wind_data'], "{:.0f}kmh".format(ac_data['wind_speed']))
    ac.setText(labels['road_data'], "{:.0f}C".format(ac_data['road_temp']))
    ac.setText(labels['air_data'], "{:.0f}C".format(ac_data['air_temp']))

    # Draw wind arrow indicator
    draw_wind_indicator()


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
    # Done with drawing geometry
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