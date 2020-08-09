import ac

from TrackConditionsLib.color_palette import Colors
from TrackConditionsLib.config_handler import Config
from TrackConditionsLib.ac_data import Session, Car
from TrackConditionsLib.drawables import WindIndicator
from TrackConditionsLib.app_window import AppWindow
from TrackConditionsLib.ac_label import ACLabel
from TrackConditionsLib.ac_gl_utils import Point

# Initialize general object variables
cfg = None
session = None
app_window = None
wind_indicator = None

# Timers
timer_30_hz = 0
PERIOD_30_HZ = 1 / 30
timer_1_hz = 0
PERIOD_1_HZ = 1

# Text labels
label_grip_text = None
label_wind_text = None
label_road_text = None
label_air_text = None

label_grip_val = None
label_wind_val = None
label_road_val = None
label_air_val = None

def acMain(ac_version):
    """Run upon startup of Assetto Corsa.
    
    Args:
        ac_version (str): Version of Assetto Corsa.
            AC passes this argument automatically.
    """
    # Read config
    global cfg
    cfg = Config()

    # Initialize session data object
    global session
    session = Session(cfg)

    # Set up app window
    global app_window
    app_window = AppWindow(cfg)
    ac.addRenderCallback(app_window.id, app_render)

    # Set up wind indicator object and add to list of drawables
    global wind_indicator
    wind_indicator = WindIndicator(cfg, session)
    app_window.add_drawable(wind_indicator)

    # Initialize font
    ac.initFont(0, 'ACRoboto300', 0, 0)

    # Add text labels
    global label_grip_text, label_wind_text, label_road_text, label_air_text
    label_grip_text = ACLabel(app_window.id, text="GRIP:")
    label_wind_text = ACLabel(app_window.id, text="WIND:")
    label_road_text = ACLabel(app_window.id, text="ROAD:")
    label_air_text = ACLabel(app_window.id, text="AIR:")

    text_labels_list = [label_grip_text, label_wind_text, label_road_text, label_air_text]
    for n, label in enumerate(text_labels_list):
        label.set_custom_font('ACRoboto300')
        label.fit_height(
            Point(cfg.app_padding_px,
                  cfg.app_padding_px + (100 * n * cfg.app_scale)),
            100 * cfg.app_scale
        )

    global label_grip_val, label_wind_val, label_road_val, label_air_val
    label_grip_val = ACLabel(app_window.id, postfix=" %")
    label_wind_val = ACLabel(app_window.id, postfix=" km/h")
    label_road_val = ACLabel(app_window.id, postfix=" C")
    label_air_val = ACLabel(app_window.id, postfix=" C")

    data_labels_list = [label_grip_val, label_wind_val, label_road_val, label_air_val]
    for n, label in enumerate(data_labels_list):
        label.set_custom_font('ACRoboto300')
        label.set_alignment('right')
        label.fit_height(
            Point(cfg.app_height * (cfg.app_aspect_ratio - 1 - cfg.app_padding),
                  cfg.app_padding_px + (100 * n * cfg.app_scale)),
            100 * cfg.app_scale
        )


def acUpdate(deltaT):
    """Run every physics tick of Assetto Corsa.
    
    Args:
        deltaT (float): Time delta since last tick in seconds.
            Assetto Corsa passes this argument automatically.

    Important: Function gets called regardless of app being visible.
    """
    pass


def app_render(deltaT):
    """Run every rendered frame of Assetto Corsa.

    Args:
        deltaT (float): Time delta since last tick in seconds.
            Assetto Corsa passes this argument automatically.

    Important: Function only gets called if the app is visible.
    """
    global timer_30_hz, timer_1_hz
    # Update timers
    timer_30_hz += deltaT
    timer_1_hz += deltaT

    # Run on 1hz
    if timer_1_hz > PERIOD_1_HZ:
        timer_1_hz -= PERIOD_1_HZ

        # Update text labels.
        # If replay, display empty text labels
        if session.status == 1:
            label_grip_val.set_text("-")
            label_wind_val.set_text("-")
            label_road_val.set_text("-")
            label_air_val.set_text("-")
        else:
            label_grip_val.set_text("{:.1f}".format(session.track_grip))
            label_wind_val.set_text("{:.0f}".format(session.wind_speed))
            label_road_val.set_text("{:.0f}".format(session.road_temp))
            label_air_val.set_text("{:.0f}".format(session.air_temp))

    # Run on 30hz
    if timer_30_hz > PERIOD_30_HZ:
        timer_30_hz -= PERIOD_30_HZ

        # Update AC data
        session.update()

        # Update WindIndicator model
        wind_indicator.update()

    # Draw graphics on app window
    app_window.draw()


def acShutdown():
    """Run on shutdown of Assetto Corsa"""
    # Update config if necessary
    if cfg.update_cfg:
        cfg.save()