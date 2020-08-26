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
        
        # Center of rotation coordinates
        self.cor = Point(
            self.cfg.app_width - (self.cfg.app_height / 2),
            self.cfg.app_height / 2)

        # Radius of the arrow, used to scale it.
        self.radius = self.cfg.app_height * (0.5 - (self.cfg.app_padding * 1.5))

        # Building the base arrow which gets rotated with every update.
        # First, arrow is built around center x,y 0,0.
        # Next, the arrow is scaled to the specified radius
        # Finally, it is moved in position by addition of the CoR coords to it.

        # Arrow is made up of head and shaft.
        # Head is split in left and right hand side: lhs & rhs,
        # and a center piece.
        self.arrow_head_tip = Point(0, -21)

        self.arrow_head_rhs_t = Point(15.5, -6)
        self.arrow_head_rhs_b = Point(15.5, 3)
        
        self.arrow_head_lhs_t = Point(-15.5, -6)
        self.arrow_head_lhs_b = Point(-15.5, 3)

        self.arrow_shaft_tl = Point(-3.5, -9)
        self.arrow_shaft_tr = Point(3.5, -9)
        self.arrow_shaft_br = Point(3.5, 21)
        self.arrow_shaft_bl = Point(-3.5, 21)

        # Right hand side of the arrow head
        self.arrow_head_rhs = Quad(
            self.arrow_head_tip,
            self.arrow_shaft_tr,
            self.arrow_head_rhs_b,
            self.arrow_head_rhs_t
        )

        # Left hand side of the arrow head
        self.arrow_head_lhs = Quad(
            self.arrow_head_tip,
            self.arrow_head_lhs_t,
            self.arrow_head_lhs_b,
            self.arrow_shaft_tl
        )

        # Shaft of the arrow
        self.arrow_shaft = Quad(
            self.arrow_shaft_tr,
            self.arrow_shaft_tl,
            self.arrow_shaft_bl,
            self.arrow_shaft_br
        )

        self.arrow_head_center = Quad(
            self.arrow_head_tip,
            self.arrow_shaft_tl,
            self.arrow_shaft_bl,
            self.arrow_shaft_tr
        )

        # Base shape containing all the quads that form the arrow
        _base_shape = [
            self.arrow_head_lhs,
            self.arrow_head_rhs,
            self.arrow_shaft,
            self.arrow_head_center
        ]

        self.base_shape = []
        for quad in _base_shape:
            new_quad = quad.copy()
            new_quad.multiply(self.radius / 21)
            new_quad.add(self.cor)
            self.base_shape.append(new_quad)

        # Render queue contains the shape that gets rendered
        self.render_queue = self.base_shape.copy()


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
                # From north to east/west shift color from red to yellow.
                green_value = 2 * color_shift
                # r,g,b,a tuple
                self.color = (1, green_value, 0, 1)
            else:
                # From east/west to south shift color from yellow to green.
                red_value = 1 - (color_shift - 0.5) * 2
                # r,g,b,a tuple
                self.color = (red_value, 1, 0, 1)

        _render_queue = []
        for quad in self.base_shape:
            new_quad = quad.copy()
            new_quad.rotate_rad(self.angle, self.cor)
            _render_queue.append(new_quad)

        self.render_queue = _render_queue

    def draw(self):
        """ Draw the model. """
        set_color(self.color)
        for quad in self.render_queue:
            ac.glBegin(acsys.GL.Quads)
            ac.glVertex2f(quad.points[0].x, quad.points[0].y)
            ac.glVertex2f(quad.points[1].x, quad.points[1].y)
            ac.glVertex2f(quad.points[2].x, quad.points[2].y)
            ac.glVertex2f(quad.points[3].x, quad.points[3].y)
            ac.glEnd()


def set_color(rgba):
    """ Apply RGBA color for GL drawing.

    Agrs:
        rgba (tuple): r,g,b,a on a 0-1 scale.
    """
    ac.glColor4f(rgba[0], rgba[1], rgba[2], rgba[3])
