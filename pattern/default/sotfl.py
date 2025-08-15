from ..common import assembly, calculator, copper, courtyard, mask, silkscreen


def build(pattern, element):
    housing = element['housing']
    housing['flatlead'] = True
    housing['polarized'] = True

    settings = pattern.settings
    if not getattr(pattern, 'name', None):
        comp_type = element.get('housing', {}).get('componentType', 'ICSOFL')  # ICSOFL or TRXSOFL
        pins = int(round(housing['leadCount']))
        pitch_h = int(round(housing['pitch'] * 100))
        bl = int(round(housing['bodyLength']['nom'] * 100))
        bw = int(round(housing['bodyWidth']['nom'] * 100))
        bh = int(round(housing['height']['max'] * 100))
        # Prefer max for leads if nom not provided
        ll = element['housing'].get('leadLength', {}).get('nom', element['housing'].get('leadLength', {}).get('max', element['housing'].get('leadLength', {}).get('min', 0)))
        lw = element['housing'].get('leadWidth', {}).get('nom', element['housing'].get('leadWidth', {}).get('max', element['housing'].get('leadWidth', {}).get('min', 0)))
        ll_h = int(round(ll * 100))
        lw_h = int(round(lw * 100))
        pattern.name = f"{comp_type}{pins}P{pitch_h}_{bl:03d}X{bw:03d}X{bh:03d}{ll_h:03d}X{lw_h:03d}{settings['densityLevel']}"

    # Use flatlead IPC (Table 3-22)
    pad_params = calculator.dual(pattern.__dict__, housing, 'flatlead')

    lead_count = int(housing['leadCount'])
    if lead_count not in (3, 5, 6):
        raise ValueError(f"Wrong lead count ({lead_count}) for SOTFL; expected 3, 5 or 6")

    pitch = housing['pitch']
    if lead_count == 3:
        # Leave an empty pitch between the two pads on the 2-pad side
        left_count, left_pitch = 2, 2 * pitch
        right_count, right_pitch = 1, pitch
    elif lead_count == 5:
        # Leave an empty pitch between the two pads on the 2-pad side
        left_count, left_pitch = 3, pitch
        right_count, right_pitch = 2, 2 * pitch
    else:  # 6
        left_count, left_pitch = 3, pitch
        right_count, right_pitch = 3, pitch

    pad = {
        'type': 'smd',
        'shape': 'rectangle',
        'width': pad_params['width'],
        'height': pad_params['height'],
        'layer': ['topCopper', 'topMask', 'topPaste'],
    }

    pad_left = dict(pad)
    pad_left['x'] = -pad_params['distance'] / 2
    y = -left_pitch * (left_count / 2 - 0.5)
    for i in range(1, left_count + 1):
        pad_left['y'] = y
        pattern.pad(i, pad_left)
        y += left_pitch

    pad_right = dict(pad)
    pad_right['x'] = pad_params['distance'] / 2
    y = right_pitch * (right_count / 2 - 0.5)
    for i in range(1, right_count + 1):
        pad_right['y'] = y
        pattern.pad(left_count + i, pad_right)
        y -= right_pitch

    copper.mask(pattern)
    silkscreen.dual(pattern, housing)
    assembly.polarized(pattern, housing)
    courtyard.dual(pattern, housing, pad_params['courtyard'])
    mask.dual(pattern, housing)

