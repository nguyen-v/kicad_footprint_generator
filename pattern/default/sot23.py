from ..common import assembly, calculator, copper, courtyard, mask, silkscreen


def build(pattern, element):
    housing = element['housing']
    housing['polarized'] = True
    housing['sot23'] = True  # Flag for SOT-23-specific silkscreen/assembly
    settings = pattern.settings
    flatlead = housing.get('flatlead', False)
    if not getattr(pattern, 'name', None):
        # SOT23 naming: SOT23-{leadCount}P{pitch}_{leadSpan}X{bodyWidth}X{height}L{leadLength}X{leadWidth}{density}
        pitch_h = int(round(housing['pitch'] * 100))
        ls = int(round(housing['leadSpan']['nom'] * 100))
        bw = int(round(housing['bodyWidth']['nom'] * 100))
        bl = int(round(housing['bodyLength']['nom'] * 100))
        bh = int(round(housing['height']['max'] * 100))
        
        # Use nominal values for lead dimensions
        ll = housing.get('leadLength', {}).get('nom')
        if ll is None:
            # Calculate nominal from min/max if not provided
            ll_min = housing.get('leadLength', {}).get('min', 0)
            ll_max = housing.get('leadLength', {}).get('max', 0)
            ll = (ll_min + ll_max) / 2 if ll_max > 0 else 0
        
        lw = housing.get('leadWidth', {}).get('nom')
        if lw is None:
            # Calculate nominal from min/max if not provided
            lw_min = housing.get('leadWidth', {}).get('min', 0)
            lw_max = housing.get('leadWidth', {}).get('max', 0)
            lw = (lw_min + lw_max) / 2 if lw_max > 0 else 0
        
        pattern.name = f"SOT23-{int(round(housing['leadCount']))}P{pitch_h:03d}_{ls:03d}X{bh:03d}L{int(round(ll*100)):03d}{settings['densityLevel']}"
        
        # Generate description and tags
        pin_count = int(housing['leadCount'])
        pitch = housing['pitch']
        body_w = housing['bodyWidth']['nom']
        body_l = housing['bodyLength']['nom']
        h = housing['height']['max']
        density_desc = {'L': 'Least', 'N': 'Nominal', 'M': 'Most'}[settings['densityLevel']]
        
        pattern.description = (f"Small Outline Transistor (SOT-23), {pin_count} Pin "
                             f"({pitch:.2f}mm pitch), Body {body_l:.2f}mm x {body_w:.2f}mm x {h:.2f}mm, "
                             f"Lead {ll:.2f}mm x {lw:.2f}mm, {density_desc} Density")
        pattern.tags = "sot23"

    if housing['leadCount'] % 2 == 0 and housing['leadCount'] != 6:
        from .sop import build as sop_build
        return sop_build(pattern, element)

    # Ensure leadWidth1 and leadWidth2 are set for sot() function
    if 'leadWidth1' not in housing:
        housing['leadWidth1'] = housing['leadWidth']
    if 'leadWidth2' not in housing:
        housing['leadWidth2'] = housing['leadWidth']
    
    pad_params = calculator.sot(pattern.__dict__, housing)

    if housing['leadCount'] == 3:
        left_count, left_pitch = 2, housing['pitch'] * 2
        right_count, right_pitch = 1, housing['pitch']
    elif housing['leadCount'] == 5:
        left_count, left_pitch = 3, housing['pitch']
        right_count, right_pitch = 2, housing['pitch'] * 2
    elif housing['leadCount'] == 6:
        left_count, left_pitch = 3, housing['pitch']
        right_count, right_pitch = 3, housing['pitch']
    else:
        raise ValueError(f"Wrong lead count ({housing['leadCount']})")

    pad = {
        'type': 'smd',
        'shape': 'rectangle',
        'width': pad_params['width1'],
        'height': pad_params['height1'],
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
    assembly.sot23(pattern, housing)
    courtyard.boundary_flex(pattern, housing, pad_params['courtyard'])
    mask.dual(pattern, housing)

