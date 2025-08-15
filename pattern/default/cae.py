from ..common import two_pin as tp
import math


def build(pattern, element):
    housing = element['housing']
    # Compute leadSpan from leadLength and leadSpace; if only span is provided, back-compute length
    ll = housing.get('leadLength', {})
    ls = housing.get('leadSpace', {})
    span = housing.get('leadSpan')
    if ll and ls:
        # Expect min/nom/max; compute tol as RMS of tolerances
        ll_min, ll_nom, ll_max = ll.get('min'), ll.get('nom'), ll.get('max')
        ls_min, ls_nom, ls_max = ls.get('min'), ls.get('nom'), ls.get('max')
        if None not in (ll_min, ll_nom, ll_max, ls_min, ls_nom, ls_max):
            tol = math.sqrt((ll_max - ll_min) ** 2 + (ls_max - ls_min) ** 2)
            nom = 2 * ll_nom + ls_nom
            housing['leadSpan'] = {'min': 2 * ll_min + ls_min, 'nom': nom, 'max': 2 * ll_max + ls_max, 'tol': tol}
    elif span and ls and ('min' in span and 'nom' in span and 'max' in span):
        # Derive leadLength from span and space
        ll_min = (span['min'] - ls.get('max', ls.get('nom', 0))) / 2
        ll_nom = (span['nom'] - ls.get('nom', 0)) / 2
        ll_max = (span['max'] - ls.get('min', ls.get('nom', 0))) / 2
        housing.setdefault('leadLength', {'min': ll_min, 'nom': ll_nom, 'max': ll_max, 'tol': ll_max - ll_min})
    housing['cae'] = True
    # Naming per convention: CAPAE + Base Body Size X Height + Lead Length X Width
    if not getattr(pattern, 'name', None):
        bw = int(round(housing['bodyWidth']['nom'] * 100))
        h = int(round(housing['height']['max'] * 100))
        ll = element['housing'].get('leadLength', {}).get('nom', element['housing'].get('leadLength', {}).get('max', element['housing'].get('leadLength', {}).get('min', 0)))
        lw = element['housing'].get('leadWidth', {}).get('nom', element['housing'].get('leadWidth', {}).get('max', element['housing'].get('leadWidth', {}).get('min', 0)))
        pattern.name = f"CAPAE{bw:03d}X{h:03d}{int(round(ll*100)):03d}X{int(round(lw*100)):03d}{pattern.settings['densityLevel']}"
    tp.build(pattern, element)

