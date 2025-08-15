
from ..common import calculator, courtyard, silkscreen, assembly, copper


def _resolve_range(val, prefer='nom'):
    if isinstance(val, dict):
        return val.get(prefer, val.get('max', val.get('min', 0)))
    return float(val or 0)


def build(pattern, element):
    housing = element['housing']
    settings = pattern.settings
    lead_count = int(housing.get('leadCount', 2))
    if lead_count not in (2, 3, 4):
        lead_count = 2

    # Name
    if not getattr(pattern, 'name', None):
        prefix = 'P' if 'pullBack' in housing else ''
        pattern.name = (
            f"{prefix}DFN{int(round(housing['pitch']*100))}P{int(round(housing['bodyLength']['nom']*100))}X{int(round(housing['bodyWidth']['nom']*100))}X{int(round(housing['height']['max']*100))}-{lead_count}{settings['densityLevel']}"
        )

    # Compute small pad size via SON calculator for consistency with IPC
    son_housing = dict(housing)
    # Use e1 (pitch along length) for SON pitch context if provided
    e1 = housing.get('pitch1', housing.get('pitch'))
    if e1:
        son_housing['pitch'] = e1
    pad_params = calculator.son(pattern.__dict__, son_housing)
    small_w = pad_params['width']
    small_h = pad_params['height']
    cy = pad_params['courtyard']

    # Pitches
    # e: vertical distance between small pads (along length, Y)
    # e1: horizontal distance between small pad column and large pad center (X)
    # e2: absolute X position for large pad center (optional override)
    e = float(housing.get('pitch', 0.0))
    e1 = float(housing.get('pitch1', 0.0))
    e2 = float(housing.get('pitch2', 0.0))

    # Place small pads (1 and 2), centered on y=0 unless 4-lead
    pads = []
    if lead_count in (2, 3, 4):
        # Compute positions: small column at x_small, large pad at x_large
        x_large = (e1 / 2.0) if e1 else (abs(e2) if e2 else small_w / 2.0)
        x_small = x_large - (e1 if e1 else (abs(e2) if e2 else small_w))
        # Vertical spacing by e
        y_top = e / 2.0
        y_bot = -e / 2.0
        if lead_count in (2, 3):
            # Numbering: pin 1 at lower-left (y_bot), pin 2 at upper-left (y_top)
            pads.append({'name': '1', 'x': x_small, 'y': y_bot, 'w': small_w, 'h': small_h})
            pads.append({'name': '2', 'x': x_small, 'y': y_top, 'w': small_w, 'h': small_h})
        elif lead_count == 4:
            # Two left pads and two right pads at ±(e1/2) horizontally
            x_left = -(e1 / 2.0) if e1 else -small_w
            x_right = (e1 / 2.0) if e1 else small_w
            pads.append({'name': '1', 'x': x_left, 'y': y_top, 'w': small_w, 'h': small_h})
            pads.append({'name': '2', 'x': x_left, 'y': y_bot, 'w': small_w, 'h': small_h})
            pads.append({'name': '3', 'x': x_right, 'y': y_top, 'w': small_w, 'h': small_h})
            pads.append({'name': '4', 'x': x_right, 'y': y_bot, 'w': small_w, 'h': small_h})

    # Large pad for 3-lead DFN (pad 3)
    if lead_count == 3:
        # Large pad: use dedicated largePadWidth/largePadLength instead of thermal tab
        tab_w = _resolve_range(housing.get('largePadWidth'))
        tab_l = _resolve_range(housing.get('largePadLength'))
        if tab_w > 0 and tab_l > 0:
            # Invert width/length per request and place on right side at x_large
            x_large = (e1 / 2.0) if e1 else (abs(e2) if e2 else tab_w / 2.0)
            pads.append({'name': '3', 'x': x_large, 'y': 0.0, 'w': tab_l, 'h': tab_w})

    # Emit pads
    copper.preamble(pattern, element)
    pin_num = 1
    for p in pads:
        pad = {
            'type': 'smd',
            'shape': 'rectangle',
            'x': p['x'],
            'y': p['y'],
            'width': p['w'],
            'height': p['h'],
            'layer': ['topCopper', 'topMask', 'topPaste'],
        }
        name = p.get('name') or str(pin_num)
        pattern.pad(name, pad)
        pin_num += 1 if p.get('name') is None else 0
    copper.postscriptum(pattern)

    # Graphics
    silkscreen.dual(pattern, housing)
    assembly.polarized(pattern, housing)
    courtyard.boundary(pattern, housing, cy)

