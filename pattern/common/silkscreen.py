def preamble(pattern, housing):
    line_width = pattern.settings['lineWidth']['silkscreen']
    
    # Calculate text position - above the component using real pad positions
    if 'bodyWidth' in housing and 'bodyLength' in housing:
        body_y = housing['bodyLength']['nom'] / 2
        
        # Find the actual maximum pad extent
        pad_extent = 0
        if pattern.pads:
            for pad in pattern.pads.values():
                # Calculate the farthest point of each pad from center
                pad_top = pad.y + pad.height / 2
                pad_extent = max(pad_extent, abs(pad_top))
        
        if pad_extent == 0:
            pad_extent = 0.7  # fallback if no pads found
        
        courtyard = pattern.settings.get('clearance', {}).get('courtyard', 0.25)
        text_y = -(max(body_y, pad_extent) + 1.25)
    else:
        text_y = -1.5  # fallback
    
    pattern.layer('topSilkscreen').lineWidth(line_width).attribute(
        'refDes',
        {
            'x': 0,
            'y': text_y,
            'halign': 'center',
            'valign': 'center',
        },
    )
    if 'silkscreen' in housing and housing['silkscreen']:
        # custom path support omitted for brevity
        pass
    return pattern


def chip_preamble(pattern, housing):
    """Preamble for chip components with refDes positioning following QFP-like logic"""
    line_width = pattern.settings['lineWidth']['silkscreen']
    
    # Calculate text position using real pad positions (similar to QFP)
    if pattern.pads:
        pad_extent = 0
        for pad in pattern.pads.values():
            # Calculate the farthest point of each pad from center
            # For chip (horizontal layout), use Y extent
            pad_extent = max(pad_extent, abs(pad.y) + pad.height / 2)
        
        if pad_extent == 0:
            pad_extent = 0.7  # fallback if no pads found
        
        # Use chip body dimensions for comparison
        body_y = housing['bodyWidth']['nom'] / 2  # For chip, body width becomes Y extent
        courtyard = pattern.settings.get('clearance', {}).get('courtyard', 0.25)
        text_y = -(max(body_y, pad_extent) + 1.25)
    else:
        text_y = -1.5  # fallback
    
    pattern.layer('topSilkscreen').lineWidth(line_width).attribute(
        'refDes',
        {
            'x': 0,
            'y': text_y,
            'halign': 'center',
            'valign': 'center',
        },
    )
    if 'silkscreen' in housing and housing['silkscreen']:
        # custom path support omitted for brevity
        pass
    return pattern


def body(pattern, housing):
    w = housing['bodyWidth']['nom']
    l = housing['bodyLength']['nom']
    lw = pattern.settings['lineWidth']['silkscreen']
    x = w / 2 + lw / 2
    y = l / 2 + lw / 2
    preamble(pattern, housing).rectangle(-x, -y, x, y)


def dual(pattern, housing):
    s = pattern.settings
    lw = s['lineWidth']['silkscreen']
    w = housing['bodyWidth']['nom']
    l = housing['bodyLength']['nom']
    first_pad = list(pattern.pads.values())[0]
    gap = lw / 2 + s['clearance']['padToSilk']
    x1 = -w / 2 - lw / 2
    x2 = -x1
    yb = -l / 2 - lw / 2
    xf = first_pad.x - first_pad.width / 2 - gap
    yf = first_pad.y - first_pad.height / 2 - gap
    y1 = min(yb, yf)
    y2 = -y1
    xp = first_pad.x
    yp = (yf if xp < x1 else y1) - 1.5 * lw
    preamble(pattern, housing)
    
    if housing.get('son') or housing.get('sot23') or housing.get('sop'):
        # SON/SOT-23/SOP-specific: only draw horizontal lines (top and bottom)
        # Lines should stop at body edges, not extend beyond
        body_left = -w / 2
        body_right = w / 2
        pattern.line(body_left, y1, body_right, y1)  # bottom horizontal line
        pattern.line(body_left, y2, body_right, y2)  # top horizontal line
        
        # Add pin 1 indicator similar to QFP
        if housing.get('polarized'):
            # Get first pad and silk clearance (same as QFP)
            pad1 = list(pattern.pads.values())[0]
            pad1_x = pad1.x
            pad1_y = pad1.y
            pad1_size_y = pad1.height
            silk_to_pad_clearance = s['clearance']['silkToPad']
            
            # Y position: same calculation as QFP
            dot1_y = pad1_y - pad1_size_y/2 - 0.25 - silk_to_pad_clearance
            
            # X position: align with the top-left pad x position
            if housing.get('sot23') or housing.get('sop'):
                dot1_x = pad1_x  # Aligned with the first pad's X position
            else:
                dot1_x = body_left - 0.25 - silk_to_pad_clearance
            # Circle with same dimensions as QFP
            pattern.layer('topSilkscreen').lineWidth(0.5).circle(dot1_x, dot1_y, 0.000001)
    else:
        # Standard dual: draw full rectangle
        pattern.rectangle(x1, y1, x2, y2)
    
    if housing.get('polarized') and not housing.get('son') and not housing.get('sot23') and not housing.get('sop'):
        pattern.attribute('value', {'text': pattern.name, 'x': 0, 'y': 0})
        pattern.circle(xp, yp, 0)  # polarityMark abstraction skipped; use small dot if needed


def grid_array(pattern, housing):
    s = pattern.settings
    lw = s['lineWidth']['silkscreen']
    w = housing['bodyWidth']['nom']
    l = housing['bodyLength']['nom']
    x = w / 2 + lw / 2
    y = l / 2 + lw / 2
    dx = x - housing['horizontalPitch'] * (housing['columnCount'] / 2 - 0.5)
    dy = y - housing['verticalPitch'] * (housing['rowCount'] / 2 - 0.5)
    d = min(dx, dy)
    length = min(2 * housing['horizontalPitch'], 2 * housing['verticalPitch'], x, y)
    p = preamble(pattern, housing)
    p.moveTo(-x, -y + length).lineTo(-x, -y + d).lineTo(-x + d, -y).lineTo(-x + length, -y)
    p.moveTo(x, -y + length).lineTo(x, -y).lineTo(x - length, -y)
    p.moveTo(x, y - length).lineTo(x, y).lineTo(x - length, y)
    p.moveTo(-x, y - length).lineTo(-x, y).lineTo(-x + length, y)


def pak(pattern, housing):
    s = pattern.settings
    lw = s['lineWidth']['silkscreen']
    bw = housing.get('bodyWidth', {}).get('nom', housing.get('bodyWidth', {}).get('max'))
    bl = housing.get('bodyLength', {}).get('nom', housing.get('bodyLength', {}).get('max'))
    ls = housing['leadSpan']['nom']
    tab = housing.get('tabLedge')
    if isinstance(tab, dict):
        tab_ledge = tab.get('nom', tab.get('min', tab.get('max', 0)))
    else:
        tab_ledge = tab if tab is not None else 0
    first_pad, last_pad = list(pattern.pads.values())[0], list(pattern.pads.values())[-1]
    gap = lw / 2 + s['clearance']['padToSilk']
    dx = ls / 2 - tab_ledge - bw / 2
    x1 = dx - bw / 2 - lw / 2
    x2 = dx + bw / 2 + lw / 2
    y1 = -bl / 2 - lw / 2
    y2 = -y1
    xf = first_pad.x - first_pad.width / 2 - gap
    yf = first_pad.y - first_pad.height / 2 - gap
    xt = last_pad.x - last_pad.width / 2 - gap
    yt = last_pad.y - last_pad.height / 2 - gap
    xp = first_pad.x
    yp = (yf if xp < x1 else y1) - 1.5 * lw
    preamble(pattern, housing)
    pattern.silk_rectangle(x1, y1, x2, y2) if hasattr(pattern, 'silk_rectangle') else pattern.rectangle(x1, y1, x2, y2)
    pattern.circle(xp, yp, 0)
    pattern.moveTo(x1, yf).lineTo(xf, yf).lineTo(xf, yf + first_pad.height + gap)
    if yt < y1:
        pattern.moveTo(x2, yt).lineTo(xt, yt).lineTo(xt, y1)
        pattern.moveTo(x2, -yt).lineTo(xt, -yt).lineTo(xt, -y1)

def quad(pattern, housing):
    s = pattern.settings
    silk_line_width = s['lineWidth']['silkscreen']
    silk_pad_clearance = s['clearance']['silkToPad']
    silk_pad_offset = silk_pad_clearance + silk_line_width / 2
    
    body_width = housing['bodyWidth']['nom']
    body_length = housing['bodyLength']['nom']
    
    # Debug: Identify package type
    package_type = "QFP" if housing.get('qfp') else ("QFN" if housing.get('qfn') else "CQFP")
    print(f"\nDEBUG QUAD SILKSCREEN: Package type = {package_type}")
    print(f"DEBUG: Body dimensions = {body_width:.3f} x {body_length:.3f}")
    print(f"DEBUG: Pad count = {len(list(pattern.pads.values()))}")
    
    # Get all pads to find clearance boundaries
    pads = list(pattern.pads.values())
    
    # Calculate body outline position (just outside the actual body)
    silk_fab_offset = 0.1  # small offset from body edge
    body_x = body_width / 2 + silk_fab_offset
    body_y = body_length / 2 + silk_fab_offset
    
    # Calculate corner line lengths based on available space around corners
    # Find the corner pads (closest to each corner) to determine constraints
    
    # Find pads in each quadrant closest to corners
    corner_pads = {
        'top_left': None, 'top_right': None, 
        'bottom_left': None, 'bottom_right': None
    }
    
    for pad in pads:
        # Determine which corner this pad is closest to
        if pad.x < 0 and pad.y > 0:  # Top-left quadrant
            if (corner_pads['top_left'] is None or 
                (abs(pad.x) + pad.y) < (abs(corner_pads['top_left'].x) + corner_pads['top_left'].y)):
                corner_pads['top_left'] = pad
        elif pad.x > 0 and pad.y > 0:  # Top-right quadrant
            if (corner_pads['top_right'] is None or 
                (pad.x + pad.y) < (corner_pads['top_right'].x + corner_pads['top_right'].y)):
                corner_pads['top_right'] = pad
        elif pad.x < 0 and pad.y < 0:  # Bottom-left quadrant
            if (corner_pads['bottom_left'] is None or 
                (abs(pad.x) + abs(pad.y)) < (abs(corner_pads['bottom_left'].x) + abs(corner_pads['bottom_left'].y))):
                corner_pads['bottom_left'] = pad
        elif pad.x > 0 and pad.y < 0:  # Bottom-right quadrant
            if (corner_pads['bottom_right'] is None or 
                (pad.x + abs(pad.y)) < (corner_pads['bottom_right'].x + abs(corner_pads['bottom_right'].y))):
                corner_pads['bottom_right'] = pad
    
    # Calculate corner line lengths to maintain exact clearance to nearest pads
    # Find the maximum length that maintains silk_pad_clearance from line edge to pad edge
    
    max_corner_length_x = float('inf')
    max_corner_length_y = float('inf')
    
    print(f"\nDEBUG: Body position: body_x=±{body_x:.3f}, body_y=±{body_y:.3f}")
    print(f"DEBUG: Required clearance: {silk_pad_clearance:.3f}, line width: {silk_line_width:.3f}")
    
    # Better logic for QFN: identify pads by position patterns
    # Group pads by their approximate positions to find edge pads
    top_pads = []
    bottom_pads = []
    left_pads = []
    right_pads = []
    
    # Find the extreme Y positions (top/bottom edge pads)
    max_y = max(pad.y for pad in pads)
    min_y = min(pad.y for pad in pads)
    max_x = max(pad.x for pad in pads)
    min_x = min(pad.x for pad in pads)
    
    print(f"DEBUG: Pad position ranges: Y from {min_y:.3f} to {max_y:.3f}, X from {min_x:.3f} to {max_x:.3f}")
    
    # Tolerance for grouping pads (within 0.1mm of edge)
    tolerance = 0.1
    
    for i, pad in enumerate(pads):
        print(f"DEBUG: Analyzing pad {i}: pos=({pad.x:.3f}, {pad.y:.3f}), size={pad.width:.3f}x{pad.height:.3f}")
        
        is_top = abs(pad.y - max_y) < tolerance
        is_bottom = abs(pad.y - min_y) < tolerance  
        is_left = abs(pad.x - min_x) < tolerance
        is_right = abs(pad.x - max_x) < tolerance
        
        print(f"  Top?{is_top}, Bottom?{is_bottom}, Left?{is_left}, Right?{is_right}")
        
        if is_top:
            top_pads.append(pad)
        elif is_bottom:
            bottom_pads.append(pad)
        elif is_left:
            left_pads.append(pad)
        elif is_right:
            right_pads.append(pad)
    
    print(f"DEBUG: Found {len(top_pads)} top, {len(bottom_pads)} bottom, {len(left_pads)} left, {len(right_pads)} right pads")
    
    # Process top/bottom pads for horizontal constraints
    for pads_group, group_name in [(top_pads + bottom_pads, "top/bottom")]:
        for i, pad in enumerate(pads_group):
            print(f"DEBUG: Processing {group_name} pad {i}: pos=({pad.x:.3f}, {pad.y:.3f})")
            # For horizontal corner lines: find constraint from pads on top/bottom
            # Need the OUTER edge of the pad (farthest from body center)
            pad_edge_x = abs(pad.x) + pad.width/2  # outer edge distance from center
            
            print(f"DEBUG: Pad {i} (top/bottom): pos=({pad.x:.3f}, {pad.y:.3f}), size={pad.width:.3f}x{pad.height:.3f}")
            print(f"  pad_edge_x (outer) = {pad_edge_x:.3f}")
            
            # Corner line starts at body_x and extends inward toward center
            # For max allowable length: corner_length_x = body_x - silk_line_width - silk_pad_clearance - pad_edge_x
            max_length = body_x - silk_line_width - silk_pad_clearance - pad_edge_x
            
            print(f"  calculation: {body_x:.3f} - {silk_line_width:.3f} - {silk_pad_clearance:.3f} - {pad_edge_x:.3f} = {max_length:.3f}")
            
            if max_length > 0:
                max_corner_length_x = min(max_corner_length_x, max_length)
                print(f"  updated max_corner_length_x = {max_corner_length_x:.3f}")
    
    # Process left/right pads for vertical constraints  
    for pads_group, group_name in [(left_pads + right_pads, "left/right")]:
        for i, pad in enumerate(pads_group):
            print(f"DEBUG: Processing {group_name} pad {i}: pos=({pad.x:.3f}, {pad.y:.3f})")
            # For vertical corner lines: find constraint from pads on left/right
            # Need the OUTER edge of the pad (farthest from body center)
            pad_edge_y = abs(pad.y) + pad.height/2  # outer edge distance from center
            
            print(f"DEBUG: Pad {i} (left/right): pos=({pad.x:.3f}, {pad.y:.3f}), size={pad.width:.3f}x{pad.height:.3f}")
            print(f"  pad_edge_y (outer) = {pad_edge_y:.3f}")
            
            # Corner line starts at body_y and extends inward toward center
            # For max allowable length: corner_length_y = body_y - silk_line_width - silk_pad_clearance - pad_edge_y
            max_length = body_y - silk_line_width - silk_pad_clearance - pad_edge_y
            
            print(f"  calculation: {body_y:.3f} - {silk_line_width:.3f} - {silk_pad_clearance:.3f} - {pad_edge_y:.3f} = {max_length:.3f}")
            
            if max_length > 0:
                max_corner_length_y = min(max_corner_length_y, max_length)
                print(f"  updated max_corner_length_y = {max_corner_length_y:.3f}")
    
    # Use the calculated maximum lengths, with reasonable defaults if no constraints
    corner_length_x = max_corner_length_x if max_corner_length_x != float('inf') else body_width * 0.15
    corner_length_y = max_corner_length_y if max_corner_length_y != float('inf') else body_length * 0.15
    
    # Apply maximum size limit (don't make lines longer than 30% of body)
    corner_length_x = min(corner_length_x, body_width * 0.3)
    corner_length_y = min(corner_length_y, body_length * 0.3)
    
    print(f"Calculated corner lengths (exact clearance): x={corner_length_x:.3f}, y={corner_length_y:.3f}")
    
    print(f"After 30% body constraint: x={corner_length_x:.3f}, y={corner_length_y:.3f}")
    
    # Ensure minimum line length
    min_line_length = 0.2
    corner_length_x = max(corner_length_x, min_line_length)
    corner_length_y = max(corner_length_y, min_line_length)
    
    preamble(pattern, housing)
    
    # Draw corner markers at each corner of the body
    # L-shaped markers pointing TOWARD the body center
    
    print(f"\nDEBUG: Drawing lines with lengths x={corner_length_x:.3f}, y={corner_length_y:.3f}")
    
    # Calculate actual line end positions and verify clearances
    line_end_x = body_x - corner_length_x
    line_end_y = body_y - corner_length_y
    line_edge_x = line_end_x - silk_line_width/2  # edge of line considering thickness
    line_edge_y = line_end_y - silk_line_width/2
    
    print(f"DEBUG: Line ends at: x={line_end_x:.3f}, y={line_end_y:.3f}")
    print(f"DEBUG: Line edges at: x={line_edge_x:.3f}, y={line_edge_y:.3f}")
    
    # Find nearest pads to verify clearance
    nearest_pad_x = None
    nearest_pad_y = None
    min_dist_x = float('inf')
    min_dist_y = float('inf')
    
    for pad in pads:
        if abs(pad.y) > body_length / 2:  # Top/bottom pad
            pad_edge = abs(pad.x) - pad.width/2
            dist = pad_edge - line_edge_x
            if dist < min_dist_x:
                min_dist_x = dist
                nearest_pad_x = pad
        
        if abs(pad.x) > body_width / 2:  # Left/right pad
            pad_edge = abs(pad.y) - pad.height/2
            dist = pad_edge - line_edge_y
            if dist < min_dist_y:
                min_dist_y = dist
                nearest_pad_y = pad
    
    if nearest_pad_x:
        print(f"DEBUG: Nearest X-constraining pad: pos=({nearest_pad_x.x:.3f}, {nearest_pad_x.y:.3f}), clearance={min_dist_x:.3f}")
    if nearest_pad_y:
        print(f"DEBUG: Nearest Y-constraining pad: pos=({nearest_pad_y.x:.3f}, {nearest_pad_y.y:.3f}), clearance={min_dist_y:.3f}")
    
    # Top-left corner
    pattern.line(-body_x, body_y, -body_x + corner_length_x, body_y)   # horizontal (toward right)
    pattern.line(-body_x, body_y, -body_x, body_y - corner_length_y)   # vertical (toward down)
    
    # Top-right corner  
    pattern.line(body_x, body_y, body_x - corner_length_x, body_y)     # horizontal (toward left)
    pattern.line(body_x, body_y, body_x, body_y - corner_length_y)     # vertical (toward down)
    
    # Bottom-right corner
    pattern.line(body_x, -body_y, body_x - corner_length_x, -body_y)   # horizontal (toward left)
    pattern.line(body_x, -body_y, body_x, -body_y + corner_length_y)   # vertical (toward up)
    
    # Bottom-left corner
    pattern.line(-body_x, -body_y, -body_x + corner_length_x, -body_y) # horizontal (toward right)
    pattern.line(-body_x, -body_y, -body_x, -body_y + corner_length_y) # vertical (toward up)
    
    # Add polarity marker if needed
    if housing.get('polarized'):
        # Place dot1 circle above the first pad
        pad1 = list(pattern.pads.values())[0]
        pad1_x = pad1.x
        pad1_y = pad1.y
        pad1_size_y = pad1.height
        silk_to_pad_clearance = s['clearance']['silkToPad']
        
        dot1_x = pad1_x - 0.75  # Move 0.75mm to the left
        dot1_y = pad1_y - pad1_size_y/2 - 0.25 - silk_to_pad_clearance
        
        # Circle with very small radius but thick line width for visibility
        pattern.layer('topSilkscreen').lineWidth(0.5).circle(dot1_x, dot1_y, 0.000001)


def two_pin(pattern, housing):
    s = pattern.settings
    lw = s['lineWidth']['silkscreen']
    first_pad = list(pattern.pads.values())[0]
    gap = lw / 2 + s['clearance']['padToSilk']
    
    if 'bodyWidth' in housing and 'bodyLength' in housing:
        w = housing['bodyWidth']['nom']
        l = housing['bodyLength']['nom']
        
        if housing.get('chip'):
            # For chip: KiCad-style horizontal lines between the pads (in the center gap)
            # Calculate silk line positions avoiding pads
            silk_pad_clearance = s['clearance']['silkToPad']
            silk_line_width = s['lineWidth']['silkscreen']
            silk_pad_offset = silk_pad_clearance + silk_line_width / 2
            
            # Calculate line position - between the pads horizontally
            # Pad 1 is at negative x, pad 2 is at positive x
            # We want lines in the center gap between them
            
            # Get the gap between pads
            pad1_right_edge = first_pad.x + first_pad.width / 2  # right edge of left pad
            pad2_left_edge = -first_pad.x - first_pad.width / 2  # left edge of right pad (symmetric)
            
            # Line starts after pad1 + clearance, ends before pad2 - clearance
            line_start_x = pad1_right_edge + silk_pad_offset
            line_end_x = pad2_left_edge - silk_pad_offset
            
            # Calculate Y positions - based on body outline plus small offset
            # In KiCad, lines are positioned just outside the body outline
            silk_fab_offset = 0.1  # KiCad's silk_fab_offset (typically 0.1mm)
            silk_y = w / 2 + silk_fab_offset
            
            # Only draw lines if they would be long enough and there's space between pads
            min_line_length = 0.2  # minimum 0.2mm line length
            line_length = line_end_x - line_start_x
            if line_length > min_line_length:
                # Use chip-specific preamble for refDes positioning
                chip_preamble(pattern, housing)
                # Two horizontal lines in the center gap between pads
                pattern.line(line_start_x, silk_y, line_end_x, silk_y)
                pattern.line(line_start_x, -silk_y, line_end_x, -silk_y)
                
                if housing.get('polarized'):
                    # Polarity mark near pad 1 (left side)
                    mark_x = first_pad.x - first_pad.width / 2 - silk_pad_offset - 0.1
                    pattern.circle(mark_x, 0, 0.05)
            else:
                # Lines too short, just add the preamble for refDes positioning
                chip_preamble(pattern, housing)
        else:
            # Standard two-pin orientation
            x1 = first_pad.width / 2 + gap
            x2 = w / 2 + lw / 2
            x = max(x1, x2)
            y = l / 2 + lw / 2
            preamble(pattern, housing)
            if housing.get('cae') and not housing.get('nosilk'):
                d = x2 - x1
                pattern.moveTo(-x1, -y).lineTo(-x2, -y + d).lineTo(-x2, y).lineTo(-x1, y)
                pattern.moveTo(x1, -y).lineTo(x2, -y + d).lineTo(x2, y).lineTo(x1, y)
            elif not housing.get('nosilk'):
                pattern.line(-x, -y, -x, y).line(x, -y, x, y)
                if x1 < x2:  # Molded
                    pattern.line(-x1, -y, -x2, -y).line(-x1, y, -x2, y).line(x1, -y, x2, -y).line(x1, y, x2, y)
            if housing.get('polarized') or housing.get('cae'):
                y2 = first_pad.y - first_pad.height / 2 - gap
                pattern.moveTo(-x1, -y).lineTo(-x1, y2).lineTo(x1, y2).lineTo(x1, -y)
                pattern.circle(0, y2 - 1.5 * lw, 0)
    elif 'bodyDiameter' in housing:
        r = housing['bodyDiameter']['nom'] / 2 + lw / 2
        preamble(pattern, housing)
        if not housing.get('nosilk'):
            pattern.circle(0, 0, r)
        if housing.get('polarized'):
            y = first_pad.y + first_pad.height / 2 + gap
            pattern.rectangle(-first_pad.width / 2 - gap, -r, first_pad.width / 2 + gap, y)
            pattern.circle(0, -r - 1.5 * lw, 0)

