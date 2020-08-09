import ac
import acsys
import math

from TrackConditionsLib.ac_gl_utils import Point
from TrackConditionsLib.ac_gl_utils import Line
from TrackConditionsLib.ac_gl_utils import Triangle
from TrackConditionsLib.ac_gl_utils import Quad

from TrackConditionsLib.color_palette import Colors

class WindIndicator:
    """ Example drawable class design.
    
    Args:
        cfg (obj:Config)
        session (obj:Session)
        color (tuple): r,g,b,a on a 0-1 scale.

    General layout I follow is using the following methods:
    - update: For updating the render queue if needed for a complex drawable object
    - draw: For drawing the object on the app window.
    
    If using the drawables list in the app window object, it will call .draw() on all object in the drawables list.
    """
    def __init__(self, cfg, session):
        self.cfg = cfg
        self.session = session

        self.color = Colors.grey
        self.angle = 0
        
        # Flip indicator 180 degrees (pi rad) if wind_vane_mode is false.
        # The indicator will then function as an arrow pointing where the wind is going.
        # The offset is only used at the calculation of the render queue,
        # Because color coding should be unaffected and use the original angle.
        if self.cfg.wind_vane_mode:
            self.angle_offset = 0
        else:
            self.angle_offset = math.pi

        # Center of rotation coordinates
        self.cor = Point(
            self.cfg.app_width - (self.cfg.app_height / 2),
            self.cfg.app_height / 2)

        self.radius = self.cfg.app_height * (0.5 - self.cfg.app_padding)
        # Bottom left and right corners offset in radians from the tip.
        self.width = 2.6

        # Building the wind indicator at 0 angle.
        # Tip of the indicator
        self.point_tip = Point(
            self.cor.x,
            self.cor.y - self.radius
        )

        # y axis is inverted as bigger y means lower position on the app window. therefore normally positive ccw rotation now is cw rotation.
        # Bottom left point of the indicator
        self.point_bot_left = self.point_tip.copy()
        self.point_bot_left.rotate_rad(-self.width, self.cor)

        # Bottom center point of the wind indicator
        self.point_bot_center = Point(
            self.cor.x,
            self.cor.y + 0.5 * self.radius
        )

        # Bottom right point of the indicator
        self.point_bot_right = self.point_tip.copy()
        self.point_bot_right.rotate_rad(self.width, self.cor)

        # Build base indicator
        self.base_quad = Quad(
            self.point_tip,
            self.point_bot_left,
            self.point_bot_center,
            self.point_bot_right
        )

        # Render queue contains the shape that gets rendered
        self.render_queue = self.base_quad.copy()


    def update(self):
        """ Updating the data for the drawable object. """
        # If there is no significant wind or session status is replay,
        # Then draw greyed out straight wind indicator.
        if (self.session.wind_speed < 0.1) or (self.session.status == 1):
            self.angle = 0
            self.color = Colors.grey
        else:
            self.angle = self.session.wind_dir - self.session.focused_car.heading

            # Arrow coloring from green (headwind) to yellow (sidewind) to red (tailwind).
            # self.angle can take on values between [-2pi, +2pi]
            # needs to be remapped from [-2pi, 0, 2pi] to [0, 1, 0] in a linear way
            color_shift = 1 - abs((abs(self.angle)/math.pi - 1))

            if color_shift < 0.5:
                # From north to east/west shift color from green to yellow.
                red_value = 2 * color_shift
                # r,g,b,a tuple
                self.color = (red_value, 1, 0, 1)
            else:
                # From east/west to south shift color from yellow to red.
                green_value = 1 - (color_shift - 0.5) * 2
                # r,g,b,a tuple
                self.color = (1, green_value, 0, 1)

        _render_queue = self.base_quad.copy()
        _render_queue.rotate_rad(self.angle + self.angle_offset, self.cor)
        self.render_queue = _render_queue


    def draw(self):
        """ Draw the model. """
        set_color(self.color)

        ac.glBegin(acsys.GL.Quads)
        ac.glVertex2f(self.render_queue.points[0].x, self.render_queue.points[0].y)
        ac.glVertex2f(self.render_queue.points[1].x, self.render_queue.points[1].y)
        ac.glVertex2f(self.render_queue.points[2].x, self.render_queue.points[2].y)
        ac.glVertex2f(self.render_queue.points[3].x, self.render_queue.points[3].y)
        ac.glEnd()


def set_color(rgba):
    """ Apply RGBA color for GL drawing.

    Agrs:
        rgba (tuple): r,g,b,a on a 0-1 scale.
    """
    ac.glColor4f(rgba[0], rgba[1], rgba[2], rgba[3])
