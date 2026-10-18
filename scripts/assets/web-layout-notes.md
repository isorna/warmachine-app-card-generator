# Damage Web geometry

Derived from local Warmachine App Unity 6000.4.1f1 resources and UXManager.PopulateHealth. No game artwork is included.

- healthValue1/2/3 are outer/middle/inner (O/M/I), not spiral aspects.
- Each ring creates exactly N circles, rotated by -360*i/N around its anchor.
- ringRoot is 550 x 550. All circle templates are 70 x 70 with left=-35.
- Normal outer/middle/inner bottom offsets: 206/-191/39; centers relative to anchor: -241/+156/-74.
- Web Large uses outer scale .75; middle top126 scale .725; inner top-112 scale .7. Center offsets: -241/+161/-77.
- Relevant VisualTreeAsset IDs:403 (container),433 (outer),365 (middle),455 (inner). Style IDs:277/307/239/329. IDs are research references, not runtime dependencies.
- Print layout preserves ring centers, relative radii and order. Circle radii are limited to fit the canvas and leave small gaps between adjacent circles; guide rings connect their centers. The whole diagram is vector-based.
- Validated current maximum counts: normal12/8/4, large30/16/10. Unknown larger capacities fail closed until their layout is checked.
