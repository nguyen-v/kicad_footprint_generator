IPC-7351 Footprint Generator (Python)

- Mirrors `src/pattern/default` CoffeeScript logic to keep calculations identical.
- Generates KiCad 7/9-compatible `.kicad_mod` footprints (no symbols).
- Includes a minimal Tkinter GUI for quick generation.

Usage (CLI)

```
python -m python.generate --kind soic --element element.json --out ./kicad/footprints
```

Where `element.json` minimally contains:

```
{
  "name": "SOIC_8",
  "housing": {
    "pitch": 1.27,
    "leadCount": 8,
    "leadSpan": {"nom": 5.4, "min": 5.3, "max": 5.5},
    "leadLength": {"min": 0.4, "max": 0.6},
    "leadWidth": {"min": 0.3, "max": 0.5},
    "bodyWidth": {"nom": 3.9},
    "bodyLength": {"nom": 4.9},
    "height": {"max": 1.75},
    "polarized": true
  },
  "pins": {"1": {}, "2": {}, "3": {}, "4": {}, "5": {}, "6": {}, "7": {}, "8": {}},
  "gridLetters": {"1": "A", "2": "B", "3": "C", "4": "D"},
  "library": {"pattern": {"densityLevel": "N"}}
}
```

GUI

```
python -m python.gui
```

Select kind, density, enter housing parameters, choose output directory, Generate.

Implemented kinds

- soic (dual)
- sot23 (odd pin variant logic)
- bga (grid array)

Extend by adding modules mirroring CoffeeScript files, e.g., `pattern/default/qfp.py` calling `pattern/common/quad` builder.

