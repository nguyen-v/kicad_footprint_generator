from ..common import assembly, calculator, copper, courtyard
from .chip_array import build as chip_array_build


def build(pattern, element):
    settings = pattern.settings
    housing = element['housing']
    housing['polarized'] = True

    abbr = 'OSC'
    if housing.get('corner-concave'):
        abbr += 'CC'
    elif housing.get('dfn'):
        abbr += 'DFN'
    elif housing.get('side-concave'):
        abbr += 'SC'
    elif housing.get('side-flat'):
        abbr += 'SF'

    if not getattr(pattern, 'name', None):
        if housing.get('corner-concave'):
            bl = int(round(housing['bodyLength']['nom'] * 100))
            bw = int(round(housing['bodyWidth']['nom'] * 100))
            bh = int(round(housing['height']['max'] * 100))
            # Concave corner oscillator OSOCC
            pattern.name = f"OSOCC{bl}X{bw}X{bh}{settings['densityLevel']}"
        else:
            pitch_h = int(round(housing['pitch'] * 100))
            bl = int(round(housing['bodyLength']['nom'] * 100))
            bw = int(round(housing['bodyWidth']['nom'] * 100))
            bh = int(round(housing['height']['max'] * 100))
            ll = housing.get('leadLength', {}).get('nom', housing.get('leadLength', {}).get('max', housing.get('leadLength', {}).get('min', 0)))
            lw = housing.get('leadWidth', {}).get('nom', housing.get('leadWidth', {}).get('max', housing.get('leadWidth', {}).get('min', 0)))
            if housing.get('side-concave'):
                # OSCSC + Pin Qty + P Pitch _ Body L X W X H + Lead L X W
                pattern.name = f"OSCSC{int(round(housing['leadCount']))}P{pitch_h}_{bl}X{bw}X{bh}{int(round(ll*100))}X{int(round(lw*100))}{settings['densityLevel']}"
            elif housing.get('side-flat'):
                pattern.name = f"OSCSF{int(round(housing['leadCount']))}P{pitch_h}_{bl}X{bw}X{bh}{int(round(ll*100))}X{int(round(lw*100))}{settings['densityLevel']}"
            else:
                # L-lead or C-bend could be added as OSCSL/OSCCL later if needed
                pattern.name = f"OSC{int(round(housing['leadCount']))}P{pitch_h}_{bl}X{bw}X{bh}{int(round(ll*100))}X{int(round(lw*100))}{settings['densityLevel']}"

    if housing.get('corner-concave'):
        pad_params = calculator.corner_concave(pattern.__dict__, housing)
        pad_params['distance'] = pad_params['distance1']
        housing['pitch'] = pad_params['distance2']
        housing['leadCount'] = 4
        pad_params['pad'] = {
            'type': 'smd',
            'shape': 'rectangle',
            'width': pad_params['width'],
            'height': pad_params['height'],
            'layer': ['topCopper', 'topMask', 'topPaste'],
        }
        copper.dual(pattern, element, pad_params)
        from ..common import silkscreen
        silkscreen.dual(pattern, housing)
        assembly.polarized(pattern, housing)
        courtyard.boundary(pattern, housing, pad_params['courtyard'])
    elif housing.get('dfn'):
        # Not implemented in CoffeeScript either (TODO)
        raise NotImplementedError('oscillator dfn not implemented')
    else:
        if housing.get('side-concave'):
            housing['concave'] = True
        if housing.get('side-flat'):
            housing['flat'] = True
        chip_array_build(pattern, element)

