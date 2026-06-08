# MeshScript — Domain Knowledge Index

Map of disciplines that contain well-documented geometric rules usable as instruction material.
Goal: identify where reliable, literature-grounded form rules live — not 3D models, but *descriptions of correct form*.

Each domain is rated for v1 suitability: ✓ start here / ~ later / ✗ too complex/ambiguous for early compiler.

---

## 1. Mathematical Geometry
*The bedrock. Unambiguous, computable, falsifiable.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Platonic & Archimedean solids | Vertices, faces, edge ratios, duality | Coxeter — *Regular Polytopes* | ✓ |
| Prisms, antiprisms, Johnson solids | Extrusion, rotational symmetry | OEIS, Mathworld | ✓ |
| Minimal surfaces | Catenoid, helicoid, gyroid, Schwarz-P | Nitsche — *Lectures on Minimal Surfaces* | ~ |
| Knot theory | Torus knots, braid groups, crossing number | Adams — *The Knot Book* | ~ |
| Fractal geometry | L-systems, IFS, Mandelbulb | Mandelbrot — *The Fractal Geometry of Nature* | ✗ |
| Symmetry groups / Wallpaper groups | 17 plane symmetries, 230 space groups | Shubnikov & Koptsik — *Symmetry in Science and Art* | ~ |
| Differential geometry | Gaussian curvature, geodesics, surfaces of revolution | Do Carmo — *Differential Geometry of Curves and Surfaces* | ~ |
| Voronoi / Delaunay | Cell decomposition, dual graphs | de Berg et al. — *Computational Geometry* | ~ |

---

## 2. Precision Manufacturing & Mechanical Engineering
*Clear standards. Every dimension has a reason. Massive rule density.*

| Sub-domain | Geometric vocabulary | Literature / Standards | v1? |
|---|---|---|---|
| Fasteners (bolts, nuts, screws) | Thread profile (60° V, Acme), pitch, head geometry | ISO 68-1, ANSI B1.1, Machinery's Handbook | ✓ |
| Gears | Involute tooth profile, module, pressure angle, addendum/dedendum | AGMA 2001, ISO 6336, Shigley's | ✓ |
| Bearings & shafts | Tolerance fits (H7/p6), shoulder geometry, keyways | ISO 286, SKF Engineering Handbook | ~ |
| Sheet metal | Bend radius, K-factor, flat pattern, relief cuts | SME Sheet Metal Handbook | ~ |
| Injection moulding rules | Draft angles (1–3°), wall thickness, rib geometry, sink marks | Rosato — *Injection Molding Handbook* | ~ |
| CNC machining constraints | Min tool radius, pocket depth:width ratio, undercuts | Boothroyd & Dewhurst — *Product Design for Manufacture* | ~ |
| GD&T | Flatness, cylindricity, true position, datum structure | ASME Y14.5-2018 | ✗ (inspector, not builder) |
| 3D print design rules | Overhang angle (<45°), bridge length, wall min, support geometry | Ultimaker/Prusa design guides | ✓ |

---

## 3. Classical & Parametric Architecture
*Proportional systems are explicit ratios. Extraordinary rule density in treatises.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Classical orders (Doric, Ionic, Corinthian) | Column diameter as module; entablature ratios; capital profiles | Vitruvius — *De Architectura*; Palladio — *Four Books* | ✓ |
| Gothic structural geometry | Pointed arch, flying buttress, rib vault, tracery | Fitchen — *The Construction of Gothic Cathedrals* | ~ |
| Islamic geometric patterns | Girih tiles, star polygons, zellij | Bourgoin — *Arabic Geometrical Pattern and Design* | ~ |
| Modernist proportional systems | Le Corbusier's Modulor, golden section, Fibonacci grid | Le Corbusier — *The Modulor* | ~ |
| Parametric architecture vocabulary | Attractor fields, Loft/Sweep, Panelisation, Voronoi facade | Woodbury — *Elements of Parametric Design* | ~ |
| Structural engineering forms | Arch, truss, space frame, shell, tensegrity | Salvadori — *Why Buildings Stand Up* | ~ |
| BIM element types | Wall, slab, beam, column, door/window opening | IFC4 schema (ISO 16739) | ✗ (too broad) |
| Japanese traditional joinery | Mortise-tenon variants, shachi, kanawa tsugi | Seike — *The Art of Japanese Joinery* | ~ |

---

## 4. Natural Form & Biological Geometry
*Rules exist but are probabilistic/growth-based rather than prescriptive. Harder to compile precisely.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Phyllotaxis | Fibonacci spirals, golden angle (137.5°), packing efficiency | D'Arcy Thompson — *On Growth and Form* | ~ |
| Shell geometry | Logarithmic spiral, helico-spiral, surface of revolution | Raup — *Geometric Analysis of Shell Coiling* | ~ |
| Crystallography | 7 crystal systems, unit cell, Bravais lattices, Miller indices | Hammond — *The Basics of Crystallography and Diffraction* | ~ |
| Radiolaria / Foraminifera | Geodesic sphere variants, lattice shell, spicule geometry | Haeckel — *Art Forms in Nature* | ~ |
| Bone / trabecular structure | Anisotropic lattice, stress-line alignment | Wolff's Law; Gibson & Ashby — *Cellular Solids* | ✗ |
| Tree / branching systems | L-systems, Murray's law (pipe radius), bifurcation angle | Prusinkiewicz & Lindenmayer — *The Algorithmic Beauty of Plants* | ~ |

---

## 5. Sculpture & Fine Art
*Vocabulary is less standardised — but classical sculpture has explicit proportion canons.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Classical figure proportions | 7–8 head canon, Vitruvian ratios, contraposto geometry | Vitruvius Bk III; Loomis — *Figure Drawing* | ✗ (organic) |
| Geometric abstraction | Platonic solids as art, Brancusi reductions | Bann — *The Tradition of Constructivism* | ~ |
| Origami / rigid folding | Flat-foldability (Kawasaki theorem), Miura fold, crease patterns | Lang — *Origami Design Secrets* | ~ |
| Ceramics forms | Surface of revolution (wheel-thrown), slab geometry, coiling | Norton — *Ceramics Manual* | ~ |
| Relief carving depth mapping | Projection, depth layer vocabulary | — | ✗ |

---

## 6. Digital / Game Asset Conventions
*Community-standardised; good for polygonal mesh targets.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Hard surface modeling | Bevel/chamfer conventions, edge loop placement, support loops | Arrimus 3D / FlippedNormals guides | ✓ |
| Low-poly design | Face budget, silhouette-first reduction, normal baking proxy | Polycount wiki | ✓ |
| Character topology | Edge flow for deformation, pole placement, genus | Pluralsight / CGSociety topology guides | ✗ (organic) |
| Procedural generation | WFC, L-systems, grammar-based cities, modular kits | Shaker & Wilson — *Procedural Content Generation in Games* | ~ |
| LOD strategies | Screen-space error, quadric decimation, impostor geometry | Luebke et al. — *Level of Detail for 3D Graphics* | ~ |
| UV mapping geometry | Seam placement, island packing, texel density | — | ✗ (post-mesh) |

---

## 7. Industrial & Product Design
*Ergonomics gives human-factor constraints; automotive gives surface continuity vocabulary.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Ergonomics / grip geometry | Hand span, grip diameter (30–40mm), reach envelopes | Dreyfuss — *The Measure of Man* | ~ |
| Automotive surface design | G0/G1/G2/G3 continuity, highlight lines, feature curves | Macey & Wardle — *How to Design Cars Like a Pro* | ✗ (NURBS-heavy) |
| Consumer product conventions | Min wall, snap-fit geometry, living hinge thickness | Bralla — *Design for Manufacturability Handbook* | ~ |
| Packaging geometry | Tray, sleeve, clamshell — fold patterns | — | ~ |

---

## 8. Traditional Crafts & Making
*Some of the most explicit geometric rule sets exist here — joinery especially.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Woodworking joinery | Dovetail angle (1:6–1:8 softwood/hardwood), tenon proportion rules | Krenov — *A Cabinetmaker's Notebook*; English Joinery standards | ~ |
| Blacksmithing forms | Tapers, shoulders, upset, scroll geometry | Andrews — *The Edge of the Anvil* | ~ |
| Weaving / basketry topology | Over-under interlacement, warp/weft density, twill patterns | Bain — *Celtic Art: Methods of Construction* | ~ |
| Rope / knot geometry | Bend radius, tuck count, helical pitch | Ashley — *The Ashley Book of Knots* | ✗ |

---

## 9. Scientific & Structural Systems
*Geodesics and tensegrity have precise mathematical descriptions.*

| Sub-domain | Geometric vocabulary | Literature | v1? |
|---|---|---|---|
| Geodesic structures | Frequency, chord factor, strut length, icosahedral subdivision | Fuller — *Synergetics*; Kenner — *Geodesic Math* | ~ |
| Tensegrity | Strut-to-cable ratio, minimal rigidity, prestress geometry | Motro — *Tensegrity* | ~ |
| Space frames | Node-bar topology, span:depth ratio, double-layer grid | Makowski — *Analysis, Design and Construction of Braced Domes* | ~ |
| Molecular geometry | VSEPR bond angles, sp3/sp2/sp hybridisation | Atkins — *Physical Chemistry* | ~ |
| Antenna geometry | Log-periodic, helical, fractal — wavelength ratios | Balanis — *Antenna Theory* | ✗ |

---

## Recommended v1 Scope (3 domains)

| Domain | Why first |
|---|---|
| **Mathematical solids** (Platonic, Archimedean, prisms) | Zero ambiguity. Perfect ground truth for testing compiler correctness. Short op sequences. |
| **Mechanical parts** (fasteners, gears, 3D print rules) | Clear standards, immediately useful output, tests precision. Gears alone are a rich test case. |
| **Classical architecture** (orders, arches, columns) | Compositional assembly (many parts combine into one design). Tests the `show()` checkpoint loop and hierarchical construction. |

These three cover: **mathematical ground truth → functional precision → compositional design.** Each stresses a different part of the compiler and op library.

---

## What to build toward (not v1)

Natural form (phyllotaxis, shells, crystals) is the next frontier — it requires parametric/growth-based ops that the v1 compiler won't have. Origami is interesting because rigid-foldability is mathematically checkable — a future critique target. Game asset conventions are worth adding once the compiler outputs clean topology.

The 3D VLM critic training data will come most naturally from **mechanical** (ground truth: ISO standards) and **architecture** (ground truth: treatise proportions) — these domains have *named correct answers* which is what you need for critique supervision.
