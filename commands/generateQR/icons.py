"""Built-in icon definitions drawn via Fusion sketch API.

Each icon function draws sketch geometry within a given bounding box.
The icon is centered at (cx, cy) and fits within a square of side `size`.
All coordinates are in cm (Fusion internal units).
"""

import adsk.core
import adsk.fusion
import math

# Registry of available icons
ICON_NAMES = [
    'No Icon',
    'Empty Center',
    'Heart',
    'Star',
    'Mail',
    'Globe',
    'WiFi',
    'Phone',
    'House',
    'Music Note',
    'Camera',
    'Lock',
    'Key',
    'Thumbs Up',
    'Lightning',
    'Pin',
    'User',
    'Search',
    'Share',
    'Calendar',
    'Info',
    'Custom SVG...',
]


def draw_icon(sketch, icon_name, cx, cy, size):
    """Draw a built-in icon on the sketch.

    Args:
        sketch: adsk.fusion.Sketch
        icon_name: Name from ICON_NAMES.
        cx: Center X in cm.
        cy: Center Y in cm.
        size: Bounding box side length in cm.

    Returns:
        bool: True if icon was drawn.
    """
    icon_funcs = {
        'Heart': _draw_heart,
        'Star': _draw_star,
        'Mail': _draw_mail,
        'Globe': _draw_globe,
        'WiFi': _draw_wifi,
        'Phone': _draw_phone,
        'House': _draw_house,
        'Music Note': _draw_music_note,
        'Camera': _draw_camera,
        'Lock': _draw_lock,
        'Key': _draw_key,
        'Lightning': _draw_lightning,
        'Pin': _draw_pin,
        'User': _draw_user,
        'Search': _draw_search,
        'Share': _draw_share,
        'Calendar': _draw_calendar,
        'Info': _draw_info,
    }

    func = icon_funcs.get(icon_name)
    if func:
        func(sketch, cx, cy, size)
        return True
    return False


def _p(x, y):
    """Create a Point3D."""
    return adsk.core.Point3D.create(x, y, 0)


def _draw_heart(sketch, cx, cy, size):
    """Draw a heart shape using arcs and lines."""
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    s = size * 0.45  # scale factor

    # Heart shape: two arcs on top, meeting at a point on bottom
    # Bottom point
    bottom = _p(cx, cy - s * 0.9)
    # Top center dip
    top_mid = _p(cx, cy + s * 0.3)
    # Left and right peaks
    left_peak = _p(cx - s * 0.5, cy + s * 0.8)
    right_peak = _p(cx + s * 0.5, cy + s * 0.8)
    # Side points
    left_side = _p(cx - s, cy + s * 0.2)
    right_side = _p(cx + s, cy + s * 0.2)

    # Draw as a closed polygon approximation
    pts = [
        bottom,
        _p(cx - s * 0.85, cy + s * 0.1),
        _p(cx - s * 0.85, cy + s * 0.55),
        _p(cx - s * 0.5, cy + s * 0.85),
        top_mid,
        _p(cx + s * 0.5, cy + s * 0.85),
        _p(cx + s * 0.85, cy + s * 0.55),
        _p(cx + s * 0.85, cy + s * 0.1),
    ]

    for i in range(len(pts)):
        lines.addByTwoPoints(pts[i], pts[(i + 1) % len(pts)])


def _draw_star(sketch, cx, cy, size):
    """Draw a 5-pointed star."""
    lines = sketch.sketchCurves.sketchLines
    r_outer = size * 0.45
    r_inner = size * 0.18

    pts = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pts.append(_p(x, y))

    for i in range(10):
        lines.addByTwoPoints(pts[i], pts[(i + 1) % 10])


def _draw_mail(sketch, cx, cy, size):
    """Draw an envelope/mail icon."""
    lines = sketch.sketchCurves.sketchLines
    w = size * 0.45
    h = size * 0.3

    # Envelope rectangle
    tl = _p(cx - w, cy + h)
    tr = _p(cx + w, cy + h)
    br = _p(cx + w, cy - h)
    bl = _p(cx - w, cy - h)
    lines.addByTwoPoints(tl, tr)
    lines.addByTwoPoints(tr, br)
    lines.addByTwoPoints(br, bl)
    lines.addByTwoPoints(bl, tl)

    # V flap
    mid = _p(cx, cy - h * 0.1)
    lines.addByTwoPoints(tl, mid)
    lines.addByTwoPoints(mid, tr)


def _draw_globe(sketch, cx, cy, size):
    """Draw a globe icon (circle with latitude/longitude lines)."""
    circles = sketch.sketchCurves.sketchCircles
    lines = sketch.sketchCurves.sketchLines
    r = size * 0.4
    center = _p(cx, cy)

    # Outer circle
    circles.addByCenterRadius(center, r)

    # Horizontal line
    lines.addByTwoPoints(_p(cx - r, cy), _p(cx + r, cy))

    # Vertical ellipse (meridian) approximated as two arcs
    # Simplified as a vertical line
    lines.addByTwoPoints(_p(cx, cy - r), _p(cx, cy + r))


def _draw_wifi(sketch, cx, cy, size):
    """Draw WiFi signal arcs."""
    arcs = sketch.sketchCurves.sketchArcs
    s = size * 0.4
    center = _p(cx, cy - s * 0.6)

    # Three concentric arcs
    for i, radius in enumerate([s * 0.35, s * 0.6, s * 0.85]):
        start_angle = math.pi / 4
        arc_angle = math.pi / 2
        start_pt = _p(
            cx + radius * math.cos(start_angle),
            cy - s * 0.6 + radius * math.sin(start_angle)
        )
        arcs.addByCenterStartSweep(center, start_pt, arc_angle)

    # Dot at bottom center
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(_p(cx, cy - s * 0.6), s * 0.08)


def _draw_phone(sketch, cx, cy, size):
    """Draw a phone/smartphone icon."""
    lines = sketch.sketchCurves.sketchLines
    w = size * 0.22
    h = size * 0.42

    # Rounded rectangle approximated as rectangle
    tl = _p(cx - w, cy + h)
    tr = _p(cx + w, cy + h)
    br = _p(cx + w, cy - h)
    bl = _p(cx - w, cy - h)
    lines.addByTwoPoints(tl, tr)
    lines.addByTwoPoints(tr, br)
    lines.addByTwoPoints(br, bl)
    lines.addByTwoPoints(bl, tl)

    # Screen area line
    lines.addByTwoPoints(_p(cx - w, cy + h * 0.7), _p(cx + w, cy + h * 0.7))
    lines.addByTwoPoints(_p(cx - w, cy - h * 0.7), _p(cx + w, cy - h * 0.7))


def _draw_house(sketch, cx, cy, size):
    """Draw a house icon."""
    lines = sketch.sketchCurves.sketchLines
    s = size * 0.4

    # House body
    bl = _p(cx - s, cy - s * 0.6)
    br = _p(cx + s, cy - s * 0.6)
    tr = _p(cx + s, cy + s * 0.2)
    tl = _p(cx - s, cy + s * 0.2)
    lines.addByTwoPoints(bl, br)
    lines.addByTwoPoints(br, tr)
    lines.addByTwoPoints(tl, bl)

    # Roof
    peak = _p(cx, cy + s)
    lines.addByTwoPoints(tl, peak)
    lines.addByTwoPoints(peak, tr)

    # Door
    dw = s * 0.3
    lines.addByTwoPoints(_p(cx - dw, cy - s * 0.6), _p(cx - dw, cy))
    lines.addByTwoPoints(_p(cx - dw, cy), _p(cx + dw, cy))
    lines.addByTwoPoints(_p(cx + dw, cy), _p(cx + dw, cy - s * 0.6))


def _draw_music_note(sketch, cx, cy, size):
    """Draw a music note icon."""
    lines = sketch.sketchCurves.sketchLines
    circles = sketch.sketchCurves.sketchCircles
    s = size * 0.35

    # Note head (filled circle)
    circles.addByCenterRadius(_p(cx - s * 0.2, cy - s * 0.7), s * 0.3)

    # Stem
    lines.addByTwoPoints(
        _p(cx + s * 0.1, cy - s * 0.7),
        _p(cx + s * 0.1, cy + s * 0.8)
    )

    # Flag
    lines.addByTwoPoints(
        _p(cx + s * 0.1, cy + s * 0.8),
        _p(cx + s * 0.5, cy + s * 0.4)
    )


def _draw_camera(sketch, cx, cy, size):
    """Draw a camera icon."""
    lines = sketch.sketchCurves.sketchLines
    circles = sketch.sketchCurves.sketchCircles
    s = size * 0.4

    # Camera body
    bl = _p(cx - s, cy - s * 0.5)
    br = _p(cx + s, cy - s * 0.5)
    tr = _p(cx + s, cy + s * 0.3)
    tl = _p(cx - s, cy + s * 0.3)
    lines.addByTwoPoints(bl, br)
    lines.addByTwoPoints(br, tr)
    lines.addByTwoPoints(tr, tl)
    lines.addByTwoPoints(tl, bl)

    # Top bump (viewfinder)
    lines.addByTwoPoints(_p(cx - s * 0.3, cy + s * 0.3), _p(cx - s * 0.3, cy + s * 0.6))
    lines.addByTwoPoints(_p(cx - s * 0.3, cy + s * 0.6), _p(cx + s * 0.3, cy + s * 0.6))
    lines.addByTwoPoints(_p(cx + s * 0.3, cy + s * 0.6), _p(cx + s * 0.3, cy + s * 0.3))

    # Lens circle
    circles.addByCenterRadius(_p(cx, cy - s * 0.1), s * 0.3)


def _draw_lock(sketch, cx, cy, size):
    """Draw a padlock icon."""
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    s = size * 0.35

    # Lock body rectangle
    bl = _p(cx - s * 0.7, cy - s * 0.8)
    br = _p(cx + s * 0.7, cy - s * 0.8)
    tr = _p(cx + s * 0.7, cy + s * 0.1)
    tl = _p(cx - s * 0.7, cy + s * 0.1)
    lines.addByTwoPoints(bl, br)
    lines.addByTwoPoints(br, tr)
    lines.addByTwoPoints(tr, tl)
    lines.addByTwoPoints(tl, bl)

    # Shackle (arch on top)
    shackle_left = _p(cx - s * 0.4, cy + s * 0.1)
    shackle_right = _p(cx + s * 0.4, cy + s * 0.1)
    shackle_center = _p(cx, cy + s * 0.1)
    arcs.addByCenterStartSweep(shackle_center, shackle_left, math.pi)


def _draw_key(sketch, cx, cy, size):
    """Draw a key icon."""
    lines = sketch.sketchCurves.sketchLines
    circles = sketch.sketchCurves.sketchCircles
    s = size * 0.4

    # Key head (circle)
    circles.addByCenterRadius(_p(cx - s * 0.5, cy), s * 0.35)

    # Key shaft
    lines.addByTwoPoints(_p(cx - s * 0.15, cy), _p(cx + s * 0.9, cy))

    # Key teeth
    lines.addByTwoPoints(_p(cx + s * 0.5, cy), _p(cx + s * 0.5, cy - s * 0.3))
    lines.addByTwoPoints(_p(cx + s * 0.7, cy), _p(cx + s * 0.7, cy - s * 0.2))


def _draw_lightning(sketch, cx, cy, size):
    """Draw a lightning bolt."""
    lines = sketch.sketchCurves.sketchLines
    s = size * 0.4

    pts = [
        _p(cx - s * 0.1, cy + s),
        _p(cx - s * 0.5, cy + s * 0.1),
        _p(cx - s * 0.05, cy + s * 0.15),
        _p(cx + s * 0.1, cy - s),
        _p(cx + s * 0.5, cy - s * 0.1),
        _p(cx + s * 0.05, cy - s * 0.15),
    ]

    for i in range(len(pts)):
        lines.addByTwoPoints(pts[i], pts[(i + 1) % len(pts)])


def _draw_pin(sketch, cx, cy, size):
    """Draw a location pin icon."""
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    circles = sketch.sketchCurves.sketchCircles
    s = size * 0.4

    # Pin point at bottom
    bottom = _p(cx, cy - s)

    # Sides converging to bottom
    left = _p(cx - s * 0.6, cy + s * 0.1)
    right = _p(cx + s * 0.6, cy + s * 0.1)
    lines.addByTwoPoints(left, bottom)
    lines.addByTwoPoints(bottom, right)

    # Semicircle on top
    center_arc = _p(cx, cy + s * 0.1)
    arcs.addByCenterStartSweep(center_arc, right, math.pi)

    # Inner dot
    circles.addByCenterRadius(_p(cx, cy + s * 0.2), s * 0.2)


def _draw_user(sketch, cx, cy, size):
    """Draw a user/person icon."""
    circles = sketch.sketchCurves.sketchCircles
    arcs = sketch.sketchCurves.sketchArcs
    s = size * 0.4

    # Head
    circles.addByCenterRadius(_p(cx, cy + s * 0.4), s * 0.35)

    # Body (arc)
    body_center = _p(cx, cy - s * 0.8)
    body_start = _p(cx - s * 0.7, cy - s * 0.4)
    arcs.addByCenterStartSweep(body_center, body_start, -math.pi)


def _draw_search(sketch, cx, cy, size):
    """Draw a magnifying glass icon."""
    circles = sketch.sketchCurves.sketchCircles
    lines = sketch.sketchCurves.sketchLines
    s = size * 0.35

    # Glass circle
    circles.addByCenterRadius(_p(cx - s * 0.15, cy + s * 0.15), s * 0.55)

    # Handle
    angle = -math.pi / 4  # 45 degrees down-right
    handle_start_x = cx - s * 0.15 + s * 0.55 * math.cos(angle)
    handle_start_y = cy + s * 0.15 + s * 0.55 * math.sin(angle)
    handle_end_x = handle_start_x + s * 0.5 * math.cos(angle)
    handle_end_y = handle_start_y + s * 0.5 * math.sin(angle)
    lines.addByTwoPoints(
        _p(handle_start_x, handle_start_y),
        _p(handle_end_x, handle_end_y)
    )


def _draw_share(sketch, cx, cy, size):
    """Draw a share icon (three nodes connected)."""
    circles = sketch.sketchCurves.sketchCircles
    lines = sketch.sketchCurves.sketchLines
    s = size * 0.35
    r = s * 0.2

    # Three dots
    top_right = _p(cx + s * 0.6, cy + s * 0.5)
    middle_left = _p(cx - s * 0.6, cy)
    bottom_right = _p(cx + s * 0.6, cy - s * 0.5)

    circles.addByCenterRadius(top_right, r)
    circles.addByCenterRadius(middle_left, r)
    circles.addByCenterRadius(bottom_right, r)

    # Connection lines
    lines.addByTwoPoints(middle_left, top_right)
    lines.addByTwoPoints(middle_left, bottom_right)


def _draw_calendar(sketch, cx, cy, size):
    """Draw a calendar icon."""
    lines = sketch.sketchCurves.sketchLines
    s = size * 0.4

    # Calendar body
    bl = _p(cx - s, cy - s)
    br = _p(cx + s, cy - s)
    tr = _p(cx + s, cy + s * 0.7)
    tl = _p(cx - s, cy + s * 0.7)
    lines.addByTwoPoints(bl, br)
    lines.addByTwoPoints(br, tr)
    lines.addByTwoPoints(tr, tl)
    lines.addByTwoPoints(tl, bl)

    # Header line
    lines.addByTwoPoints(_p(cx - s, cy + s * 0.3), _p(cx + s, cy + s * 0.3))

    # Hanging tabs
    lines.addByTwoPoints(_p(cx - s * 0.5, cy + s * 0.7), _p(cx - s * 0.5, cy + s))
    lines.addByTwoPoints(_p(cx + s * 0.5, cy + s * 0.7), _p(cx + s * 0.5, cy + s))


def _draw_info(sketch, cx, cy, size):
    """Draw an info (i) icon."""
    circles = sketch.sketchCurves.sketchCircles
    lines = sketch.sketchCurves.sketchLines
    s = size * 0.4

    # Outer circle
    circles.addByCenterRadius(_p(cx, cy), s)

    # Dot for i
    circles.addByCenterRadius(_p(cx, cy + s * 0.4), s * 0.1)

    # Vertical line for i
    lines.addByTwoPoints(_p(cx, cy + s * 0.15), _p(cx, cy - s * 0.45))
