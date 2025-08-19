from . import calculator
from . import copper
from . import courtyard
from . import silkscreen
from . import mask

# helper facades mirroring Coffee structure

class grid_array:
    @staticmethod
    def build(pattern, element):
        from . import calculator as calc
        from . import copper as cu
        from . import courtyard as cy
        from . import assembly as asm
        from . import silkscreen as ss
        housing = element['housing']
        settings = pattern.settings
        lead_count = housing.get('leadCount') or len(element['pins'])
        # Ensure pitch is present without touching absent horizontal/vertical pitch
        if 'pitch' not in housing:
            hp = housing.get('horizontalPitch')
            vp = housing.get('verticalPitch')
            if hp is not None and vp is not None:
                housing['pitch'] = max(hp, vp)
        if housing.get('cga'):
            abbr, option = 'CGA', 'cga'
        elif housing.get('lga'):
            abbr, option = 'LGA', 'lga'
        else:
            abbr, option = 'BGA', 'bga'
        if not getattr(pattern, 'name', None):
            if option == 'bga':
                pitch = int(round(housing['pitch'] * 100))
                cols = housing['columnCount']
                rows = housing['rowCount']
                bl = int(round(housing['bodyLength']['nom'] * 100))
                bw = int(round(housing['bodyWidth']['nom'] * 100))
                bh = int(round(housing['height']['max'] * 100))
                # ball diameter (nom)
                bd_src = housing.get('leadDiameter', {})
                bd = bd_src.get('nom', bd_src.get('max', bd_src.get('min', 0))) if isinstance(bd_src, dict) else float(bd_src or 0)
                bd_h = int(round(bd * 100))
                cn = 'C' if settings['ball']['collapsible'] else 'N'
                pattern.name = f"BGA{lead_count}{cn}P{pitch}_{cols}X{rows}_{bl:03d}X{bw:03d}X{bh:03d}{bd_h:03d}{settings['densityLevel']}"
            elif option in ('cga','lga'):
                pitch = int(round(housing['pitch'] * 100))
                cols = housing['columnCount']
                rows = housing['rowCount']
                bl = int(round(housing['bodyLength']['nom'] * 100))
                bw = int(round(housing['bodyWidth']['nom'] * 100))
                bh = int(round(housing['height']['max'] * 100))
                ld_src = housing.get('leadDiameter', {})
                ld = ld_src.get('nom', ld_src.get('max', ld_src.get('min', 0))) if isinstance(ld_src, dict) else float(ld_src or 0)
                ld_h = int(round(ld * 100))
                pattern.name = f"{abbr}{lead_count}P{pitch}_{cols}X{rows}_{bl:03d}X{bw:03d}X{bh:03d}{ld_h:03d}{settings['densityLevel']}"
        housing.setdefault('verticalPitch', housing['pitch'])
        housing.setdefault('horizontalPitch', housing['pitch'])
        pad_params = calc.grid_array(pattern.__dict__, housing, option)
        pad = {
            'type': 'smd',
            'width': pad_params['width'],
            'height': pad_params['height'],
            'shape': 'rectangle' if housing.get('lga') else 'circle',
            'layer': ['topCopper', 'topMask', 'topPaste'],
        }
        cu.grid_array(pattern, element, pad)
        ss.grid_array(pattern, housing)
        asm.body(pattern, housing)
        cy.grid_array(pattern, housing, pad_params['courtyard'])


class dual:
    @staticmethod
    def build(pattern, element):
        from . import calculator as calc
        from . import copper as cu
        from . import courtyard as cy
        from . import silkscreen as ss
        from . import mask as mk
        housing = element['housing']
        settings = pattern.settings
        lead_count = 0
        has_tab = ('tabWidth' in housing) and ('tabLength' in housing)
        for i in range(0, housing['leadCount'] + (1 if has_tab else 0) + 1):
            if str(i) in element['pins']:
                lead_count += 1
        if housing.get('cfp'):
            abbr, option = 'CFP', 'sop'
        elif housing.get('flatlead'):
            abbr, option = 'SOPFL', 'flatlead'
        elif housing.get('soic'):
            abbr, option = 'SOIC', 'sop'
            housing['soic'] = True  # Ensure flag is set for assembly detection
        elif housing.get('soj'):
            abbr, option = 'SOJ', 'soj'
        elif housing.get('sol'):
            abbr, option = 'SOL', 'sol'
        elif housing.get('son'):
            abbr, option = 'SON', 'son'
        else:
            abbr, option = 'SOP', 'sop'
        if not getattr(pattern, 'name', None):
            pitch_h = int(round(housing['pitch'] * 100))
            ls = int(round(housing['leadSpan']['nom'] * 100))
            bw = int(round(housing['bodyWidth']['nom'] * 100))
            bh = int(round(housing['height']['max'] * 100))
            ll = housing.get('leadLength', {}).get('nom', housing.get('leadLength', {}).get('max', housing.get('leadLength', {}).get('min', 0)))
            lw = housing.get('leadWidth', {}).get('nom', housing.get('leadWidth', {}).get('max', housing.get('leadWidth', {}).get('min', 0)))
            ll_h = int(round(ll * 100))
            lw_h = int(round(lw * 100))
            # Map to naming conventions
            name_base = abbr
            if abbr == 'SOPFL' and housing.get('flatlead') and ('leadCount' in housing) and housing['leadCount'] in (3, 4, 5, 6):
                # ICSOFL/TRXSOFL handled in sotfl builder; fallback SOPFL here
                name_base = 'SOPFL'
            if abbr == 'SOIC':
                # SOIC naming: SOIC4P250_640X390X290L110X84N
                pattern.name = f"{name_base}{lead_count}P{pitch_h}_{ls}X{bw}X{bh}L{ll_h}X{lw_h}{settings['densityLevel']}"
            else:
                pattern.name = f"{name_base}{lead_count}P{pitch_h}_{ls}X{bw}X{bh}{ll_h}X{lw_h}{settings['densityLevel']}"
        pad_params = calc.dual(pattern.__dict__, housing, option)
        pad_params['order'] = 'round'
        pad_params['pad'] = {
            'type': 'smd',
            'shape': 'rectangle',
            'width': pad_params['width'],
            'height': pad_params['height'],
            'layer': ['topCopper', 'topMask', 'topPaste'],
        }
        cu.dual(pattern, element, pad_params)
        ss.dual(pattern, housing)
        if housing.get('polarized'):
            from . import assembly as asm
            if housing.get('soic'):
                # SOIC uses SOP-style assembly (no chamfer, pin1 dot)
                asm.sop(pattern, housing)
            else:
                asm.polarized(pattern, housing)
        else:
            from . import assembly as asm
            asm.body(pattern, housing)
        cy.dual(pattern, housing, pad_params['courtyard'])
        mk.dual(pattern, housing)
        from . import copper as cu2
        cu2.tab(pattern, element) if hasattr(cu2, 'tab') else None


class quad:
    @staticmethod
    def build(pattern, element):
        from . import calculator as calc
        from . import copper as cu
        from . import courtyard as cy
        from . import silkscreen as ss
        from . import mask as mk
        from . import assembly as asm
        housing = element['housing']
        settings = pattern.settings
        lead_count = housing.get('leadCount')
        if lead_count is None:
            rc = int(housing.get('rowCount', 0) or 0)
            cc = int(housing.get('columnCount', 0) or 0)
            lead_count = 2 * (rc + cc) if (rc and cc) else len(element['pins'])
        has_tab = ('tabWidth' in housing) and ('tabLength' in housing)
        if has_tab:
            lead_count += 1
        housing.setdefault('columnSpan', housing.get('leadSpan'))
        housing.setdefault('rowSpan', housing.get('leadSpan'))

        if housing.get('cqfp'):
            abbr, option = 'CQFP', 'qfp'
            length = housing['rowSpan']['nom']
            width = housing['columnSpan']['nom']
        elif housing.get('qfn'):
            # Distinguish between QFN and PQFN based on PQFN flag
            if housing.get('pqfn'):
                abbr = 'PQFN'  # Pullback QFN
            else:
                abbr = 'QFN'   # Standard QFN (no pullback)
            option = 'qfn'
            length = housing['bodyLength']['nom']
            width = housing['bodyWidth']['nom']
        else:
            abbr, option = 'QFP', 'qfp'
            length = housing['columnSpan']['nom']
            width = housing['rowSpan']['nom']

        if not getattr(pattern, 'name', None):
            pitch_h = int(round(housing['pitch'] * 100))
            l_h = int(round(length * 100))
            w_h = int(round(width * 100))
            h_h = int(round(housing['height']['max'] * 100))
            # derive lead length/width for suffix (use nominal values preferentially)
            ll = housing.get('leadLength', {}).get('nom', housing.get('leadLength', {}).get('max', housing.get('leadLength', {}).get('min', 0)))
            lw = housing.get('leadWidth', {}).get('nom', housing.get('leadWidth', {}).get('max', housing.get('leadWidth', {}).get('min', 0)))
            ll_h = int(round(ll * 100))
            lw_h = int(round(lw * 100))
            # Thermal pad indicator for QFN family
            t_suffix = ''
            if option == 'qfn':
                tw = housing.get('tabWidth')
                tl = housing.get('tabLength')
                # consider present when any non-zero nominal exists
                def _nom(v):
                    if isinstance(v, dict):
                        return v.get('nom', v.get('max', v.get('min', 0)))
                    return v
                if (_nom(tw) or 0) > 0 and (_nom(tl) or 0) > 0:
                    t_suffix = f"T{int(round(_nom(tl)*100))}X{int(round(_nom(tw)*100))}"
            # Final name per table: ABBR + PinQty + P Pitch _ L X W X H + L + LeadLen X LeadW (+ T...)
            # Use actual pin count (exclude thermal pad from pin count in name)
            actual_pin_count = housing.get('leadCount')
            if actual_pin_count is None:
                rc = int(housing.get('rowCount', 0) or 0)
                cc = int(housing.get('columnCount', 0) or 0)
                actual_pin_count = 2 * (rc + cc) if (rc and cc) else len(element['pins'])
            pattern.name = f"{abbr}{actual_pin_count}P{pitch_h:03d}_{l_h:03d}X{w_h:03d}X{h_h:03d}L{ll_h:03d}X{lw_h:03d}{t_suffix}{settings['densityLevel']}"
            
            # Generate description and tags for QFN/QFP packages
            pitch = housing['pitch']
            h = housing['height']['max']
            density_desc = {'L': 'Least', 'N': 'Nominal', 'M': 'Most'}[settings['densityLevel']]
            
            thermal_desc = ""
            if t_suffix:  # Thermal pad present
                tw = housing.get('tabWidth')
                tl = housing.get('tabLength')
                def _nom(v):
                    if isinstance(v, dict):
                        return v.get('nom', v.get('max', v.get('min', 0)))
                    return v
                thermal_desc = f", Thermal Pad {_nom(tl):.2f}mm x {_nom(tw):.2f}mm"
            
            if option == 'qfn':
                if housing.get('pqfn'):
                    package_desc = "Pullback Quad Flat No-Lead (PQFN)"
                    tags = "pqfn ic"
                else:
                    package_desc = "Quad Flat No-Lead (QFN)"
                    tags = "qfn ic"
            elif option == 'qfp':
                package_desc = "Quad Flat Package (QFP)"
                tags = "qfp ic"
            else:  # cqfp
                package_desc = "Ceramic Quad Flat Package (CQFP)"
                tags = "cqfp ic"
            
            pattern.description = (f"{package_desc}, {actual_pin_count} Pin "
                                 f"({pitch:.2f}mm pitch), Body {length:.2f}mm x {width:.2f}mm x {h:.2f}mm, "
                                 f"Lead {ll:.2f}mm x {lw:.2f}mm{thermal_desc}, {density_desc} Density")
            pattern.tags = tags

        pad_params = calc.quad(pattern.__dict__, housing, option)
        row_pad = {
            'type': 'smd',
            'shape': 'rectangle',
            'width': pad_params['width1'],
            'height': pad_params['height1'],
            'distance': pad_params['distance1'],
            'layer': ['topCopper', 'topMask', 'topPaste'],
        }
        column_pad = {
            'type': 'smd',
            'shape': 'rectangle',
            'width': pad_params['height2'],
            'height': pad_params['width2'],
            'distance': pad_params['distance2'],
            'layer': ['topCopper', 'topMask', 'topPaste'],
        }
        cu.quad(pattern, element, {
            'rowPad': row_pad,
            'columnPad': column_pad,
            'distance1': pad_params['distance1'],
            'distance2': pad_params['distance2'],
        })
        ss.quad(pattern, housing)
        asm.quad(pattern, housing)
        # Flexible courtyard around body and pads (step 1: separate rectangles)
        cy.boundary_flex(pattern, housing, pad_params['courtyard'])
        mk.quad(pattern, housing)
        cu.tab(pattern, element)


class two_pin:
    @staticmethod
    def build(pattern, element):
        from . import calculator as calc
        from . import courtyard as cy
        from . import silkscreen as ss
        from . import assembly as asm
        from . import mask as mk
        housing = element['housing']
        settings = pattern.settings
        height = housing.get('height', {}).get('max', housing.get('bodyDiameter', {}).get('max'))

        # Determine abbr and option
        abbr = 'U'
        option = 'chip'
        if housing.get('cae'):
            abbr += 'AE'
            option = 'crystal'
            size = f"{int(round(housing['bodyWidth']['nom']*100))}X{int(round(height*100))}"
        elif housing.get('concave'):
            abbr += 'SC'
            option = 'concave'
            size = f"{int(round(housing['bodyLength']['nom']*10)):02d}X{int(round(housing['bodyWidth']['nom']*10)):02d}X{int(round(height*100))}"
        elif housing.get('crystal'):
            option = 'crystal'
            size = f"{int(round(housing['bodyLength']['nom']*10)):02d}X{int(round(housing['bodyWidth']['nom']*10)):02d}X{int(round(height*100))}"
        elif housing.get('dfn'):
            abbr += 'DFN'
            option = 'dfn'
            size = f"{int(round(housing['bodyLength']['nom']*10)):02d}X{int(round(housing['bodyWidth']['nom']*10)):02d}X{int(round(height*100))}"
        elif housing.get('molded'):
            abbr += 'M'
            option = 'molded'
            size = f"{int(round(housing['bodyLength']['nom']*10)):02d}{int(round(housing['bodyWidth']['nom']*10)):02d}X{int(round(height*100))}"
        elif housing.get('melf'):
            abbr += 'MELF'
            option = 'melf'
            # Accept bodyDiameter or bodyWidth for cylindrical MELF
            diam_nom = housing.get('bodyDiameter', {}).get('nom') if isinstance(housing.get('bodyDiameter'), dict) else housing.get('bodyDiameter')
            if diam_nom is None:
                diam_nom = housing.get('bodyWidth', {}).get('nom') if isinstance(housing.get('bodyWidth'), dict) else housing.get('bodyWidth')
            size = f"{int(round(housing['bodyLength']['nom']*10)):02d}{int(round(diam_nom*10)):02d}"
        elif housing.get('radial'):
            abbr += 'R'
            if 'diameter' in housing:
                abbr += 'D'
            option = 'radial'
            size = f"{int(round(housing['leadSpan']['nom']*100)):02d}W{int(round(housing['leadDiameter']['nom']*100)):02d}D{int(round(housing['bodyDiameter']['nom']*100)):02d}H{int(round(housing['height']['max']*100)):02d}"
        elif housing.get('sod'):
            abbr = 'SOD'
            option = 'sod'
            size = f"{int(round(housing['leadSpan']['nom']*10)):02d}{int(round(housing['bodyWidth']['nom']*10)):02d}X{int(round(height*100))}"
        elif housing.get('sodfl'):
            abbr = 'SODFL'
            option = 'sodfl'
            size = f"{int(round(housing['leadSpan']['nom']*10)):02d}{int(round(housing['bodyWidth']['nom']*10)):02d}X{int(round(height*100))}"
        else:
            abbr += 'C'
            option = 'chip'
            size = f"{int(round(housing['bodyLength']['nom']*10)):02d}{int(round(housing['bodyWidth']['nom']*10)):02d}X{int(round(height*100))}"

        if not getattr(pattern, 'name', None):
            pattern.name = f"{abbr}{size}{settings['densityLevel']}"

        pad_params = calc.two_pin(pattern.__dict__, housing, option)
        # CAE: pins must be left (1) and right (2)
        if housing.get('cae'):
            pad = {
                'shape': 'rectangle',
                'x': -pad_params['distance']/2,
                'y': 0,
                'width': pad_params['width'],
                'height': pad_params['height'],
            }
            if 'hole' in pad_params:
                if not housing.get('polarized'):
                    pad['shape'] = 'circle'
                pad['type'] = 'through-hole'
                pad['hole'] = pad_params['hole']
                pad['layer'] = ['topCopper', 'topMask', 'intCopper', 'bottomCopper', 'bottomMask']
            else:
                pad['type'] = 'smd'
                pad['layer'] = ['topCopper', 'topMask', 'topPaste']
            pattern.pad(1, pad)
            pad2 = dict(pad)
            pad2['x'] = -pad['x']
            if 'hole' in pad2:
                pad2['shape'] = 'circle'
            pattern.pad(2, pad2)
        else:
            # For chip: rotate 90° CCW so pad 1 is left, pad 2 is right (horizontal layout)
            if housing.get('chip'):
                pad = {
                    'shape': 'rectangle',
                    'x': -pad_params['distance']/2,
                    'y': 0,
                    'width': pad_params['width'],
                    'height': pad_params['height'],
                }
                if 'hole' in pad_params:
                    if not housing.get('polarized'):
                        pad['shape'] = 'circle'
                    pad['type'] = 'through-hole'
                    pad['hole'] = pad_params['hole']
                    pad['layer'] = ['topCopper', 'topMask', 'intCopper', 'bottomCopper', 'bottomMask']
                else:
                    pad['type'] = 'smd'
                    pad['layer'] = ['topCopper', 'topMask', 'topPaste']

                pattern.pad(1, pad)
                pad2 = dict(pad)
                pad2['x'] = -pad['x']
                if 'hole' in pad2:
                    pad2['shape'] = 'circle'
                pattern.pad(2, pad2)
            else:
                # CoffeeScript two-pin: placed vertically but with swapped width/height for horizontal visual
                pad = {
                    'shape': 'rectangle',
                    'x': 0,
                    'y': -pad_params['distance']/2,
                    'width': pad_params['height'],
                    'height': pad_params['width'],
                }
                if 'hole' in pad_params:
                    if not housing.get('polarized'):
                        pad['shape'] = 'circle'
                    pad['type'] = 'through-hole'
                    pad['hole'] = pad_params['hole']
                    pad['layer'] = ['topCopper', 'topMask', 'intCopper', 'bottomCopper', 'bottomMask']
                else:
                    pad['type'] = 'smd'
                    pad['layer'] = ['topCopper', 'topMask', 'topPaste']

                pattern.pad(1, pad)
                pad2 = dict(pad)
                pad2['y'] = -pad['y']
                if 'hole' in pad2:
                    pad2['shape'] = 'circle'
                pattern.pad(2, pad2)
        from . import copper as cu
        cu.mask(pattern)
        ss.two_pin(pattern, housing)
        asm.two_pin(pattern, housing)
        if housing.get('cae'):
            cy.boundary(pattern, housing, pad_params['courtyard'])
        else:
            cy.two_pin(pattern, housing, pad_params['courtyard'])
        mk.two_pin(pattern, housing)

