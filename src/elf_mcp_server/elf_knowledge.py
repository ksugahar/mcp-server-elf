"""
ELF600 electromagnetic field analysis knowledge base.

Covers file formats (.mai, .mei, .meg), three solvers (MAGIC, ELFIN, BEAM),
element types, mesh scripting, B-H curves, analysis workflows, tools,
error messages, and advanced topics (anisotropy, lamination, demagnetization,
sinusoidal response, IPM motors, inductance, magnetization).

The topics are repository-maintained engineering summaries. Product manuals,
help pages, example files, wiki text, wrappers, binaries, and solver results
are not bundled or reproduced by this module.
"""

# ============================================================
# Overview
# ============================================================

ELF_OVERVIEW = """\
# ELF600 Electromagnetic Field Analysis Suite

ELF600 is a **BEM (Boundary Element Method / Integral Element Method)**
electromagnetic analysis suite with three solver modules:

| Module | Purpose | Key Application |
|--------|---------|-----------------|
| **MAGIC** | Magnetostatic field (static, transient, AC) | Transformers, motors, magnets |
| **ELFIN** | Electrostatic field analysis | Capacitors, insulators, electrodes |
| **BEAM** | Charged particle beam tracking | Electron optics, accelerators |

**Note:** Despite the name "ELFIN", the ELFIN solver handles **electrostatic**
(not eddy current) analysis. Eddy current analysis in ELF is done by MAGIC
using MAB/MAT/MBB elements with time-stepping.

## File Types

| Extension | Description | Role |
|-----------|-------------|------|
| `.mei` | Mesh script | Procedural mesh generation language |
| `.meg` | Compiled mesh data | Node/element data (output of IEmesh) |
| `.mai` | Analysis input | Solver control, material data, SOL blocks |
| `.mao` | Computation log | Convergence info, errors, timing |
| `.mag` | Result data | Fields, forces, flux linkage |
| `.mas` | Charge/source file | For BEAM trajectory input |
| `.mat` | Matrix file | LU decomposition cache |
| `.mac` | Work file | Intermediate timestep data |
| `.model` | Motor config | Key-value config for IPM analysis |

## Workflow
```
.mei (mesh script) --> IEmesh (mesh750.exe) --> .meg (compiled mesh)
.mai (analysis) + .meg (mesh) --> MAGIC/ELFIN/BEAM --> .mag/.mao results
```

## Symmetry Types
- **T** = Full 3D
- **K** = 2D (infinite in Z, cross-section in XY plane)
- **R** = Axisymmetric (revolution about Z axis, cross-section in XZ plane)

## Tools
- **IEmesh** = Mesh script editor + mesh generator (mesh750.exe) + viewer (Wmap3)
- **MaiEditor3** = GUI editor for .mai control files
- **Wmap3** = 3D visualization of .meg and .mag files
- **MagFilter2** = Result extraction to CSV
- **ELF/Bench** = Problem/project manager with batch processing
- **ComplexTransfer2** = Convert MOMC complex results to pseudo-transient for animation
"""

# ============================================================
# .mai format
# ============================================================

MAI_FORMAT = """\
# .mai File Format (Analysis Input)

The `.mai` file controls solver execution: material properties, excitation,
solver commands, and output options.

## Structure

```
USE  <SOLVER>  3.50        # Header: MAGIC, ELFIN, or BEAM
PRE  <MAXMID> <MAXSTEP>   # Preprocessing block
  <material/excitation commands>
END
SOL <TYPE>                 # Solver execution block (repeatable)
  <solver options>
END
```

- Comment lines: first character = `*` (leading spaces/tabs OK)
- `*` before `SOL` skips that entire block
- **Max line length: 120 half-width characters**

## MAGIC PRE Keywords

### B-H Curves
| Keyword | Description | Example |
|---------|-------------|---------|
| `HBUN` | B-H curve unit (OE/G or A/M/T) | `HBUN 1 A/M T` |
| `HBSC` | B-H curve scale factors | `HBSC 1 1.0 1.0` |
| `HBCU` | B-H curve data point (H, B) | `HBCU 1 0.0 0.0` |
| `HBCN` | B-H curve assignment per step (demagnetization) | `HBCN 1 0 1` |
| `HBRM` | Recoil permeability + max remanence (demagnetization) | `HBRM 1 1.05 1.35` |
| `HBEQ` | Copy B-H curve (dest, source) | `HBEQ 2 1` |
| `HBCP` | Copy B-H curve (source, dest1, dest2, ...) | `HBCP 1 2 3 4` |

### Coil / Current
| Keyword | Description | Example |
|---------|-------------|---------|
| `COI1` | Coil definition (MID, 0, turns, NB1, NB2, A/V) | `COI1 1 0 100 8 4 A` |
| `AMP1` / `AMP1I` | Current amplitude real/imag | `AMP1 1 0 5.0` |
| `VOL1` / `VOL1I` | Voltage source real/imag | `VOL1 1 0 1.0` |
| `OHM1` | Coil resistance (normal calc) | `OHM1 1 0 0.1` |
| `OHM2` | Volume resistivity (eddy current elements) | `OHM2 3 0 2.7e-8` |
| `OHM3` / `OHM3I` | Impedance real/imag (sinusoidal calc) | `OHM3 1 0 0.1` |

### Anisotropy / Lamination
| Keyword | Description | Example |
|---------|-------------|---------|
| `HBA1` | Susceptibility anisotropy ratio (0 < k < 1) | `HBA1 1 0.5` |
| `HBA2` | Lamination stacking factor (0 < p < 1) | `HBA2 1 0.95` |
| `VEC1` | Direction vector per element (for HBA1/HBA2/MWV) | `VEC1 1 0 0.0 0.0 1.0` |
| `VEC3` | Direction vector per material | `VEC3 1 0 0.0 0.0 1.0` |

**HBA1 and HBA2 are mutually exclusive** -- cannot use both on same material.

### Thin Plate / Wire Diameter
| Keyword | Description | Example |
|---------|-------------|---------|
| `THIN` | Plate thickness [m] or wire diameter [m] | `THIN 1 0.001` |

Two uses: (1) MMT*/MAT* thin plate thickness, (2) MCL2T/MCL1* wire diameter.

### Motion
| Keyword | Description | Example |
|---------|-------------|---------|
| `MOV1` | Displacement + rotation per step | `MOV1 1 1 0.001 0 0 7.5` |
| `ORI1` | Rotation axis (origin + axis 1=X,2=Y,3=Z) | `ORI1 1 0 0 0 0 3` |
| `MVEQ` / `MVCP` | Copy motion conditions | `MVEQ 2 1` |
| `STED` | Steady-state eddy current motion | `STED 3 0 0 0 5 10` |

### Uniform Field
| Keyword | Description | Example |
|---------|-------------|---------|
| `UNI1` / `UNI1I` | Uniform field A/m (real/imag) | `UNI1 0 0 0.0 0.0 100.0` |
| `UNI2` / `UNI2I` | Uniform field Oe (real/imag) | `UNI2 0 0 0.0 0.0 1.0` |

### Complex Permeability (SOL MOMC only)
| Keyword | Description | Example |
|---------|-------------|---------|
| `CMU1` | Complex permeability real (>= 1) | `CMU1 1 0 1000.0` |
| `CMU1I` | Complex permeability imag (<= 0) | `CMU1I 1 0 -10.0` |

Replaces B-H curves for sinusoidal analysis. **Nonlinear B-H NOT supported in MOMC.**

### Output Control
| Keyword | Description | Example |
|---------|-------------|---------|
| `MAH` | Result file precision (+digit=space, -digit=comma) | `MAH 6` |
| `MAF` | Force output precision (FORT/FIXB per material) | `MAF 6` |

## ELFIN PRE Keywords
| Keyword | Description |
|---------|-------------|
| `EDSC` / `EDCU` | D-E curve scale and data points |
| `EDEQ` / `EDCP` | Copy D-E curve |
| `VOL1` | Electrode potential [V] |
| `CHA1` | Charge density [C/m^2] for EQL elements |
| `CHA2` | Total charge [C] on floating electrode (unknown potential) |
| `VAL1` | Boundary condition value (ESH: ratio, ESS/ESN: E-field) |
| `VEC2` / `VEC4` | Contour-point vector for cylindrical electrodes |

## BEAM PRE Keywords
| Keyword | Description | Example |
|---------|-------------|---------|
| `CHAR` | Particle charge [C] | `CHAR 1 1.602E-19` |
| `MASS` | Particle mass [kg] | `MASS 1 9.109E-31` |
| `VOLB` | Acceleration voltage [V] | `VOLB 1 10000.0` |
| `FILE` | Import field from MAGIC/ELFIN .mas | `FILE MAGIC problem_M` |
| `AMPB` | Beam current [A] for space-charge | `AMPB 1 0.001` |
"""

# ============================================================
# SOL commands
# ============================================================

SOL_COMMANDS = """\
# SOL Block Types and Sub-Keywords

SOL blocks define solver execution. Multiple SOL blocks can appear in one .mai.

## MAGIC SOL Types

| SOL Type | Description | After MOME | After MOMC |
|----------|-------------|------------|------------|
| `SOL MOME` | Moment method (BEM) -- main solver | -- | -- |
| `SOL MOMC` | Complex moment (sinusoidal/AC) | -- | -- |
| `SOL FIEL` | Field at evaluation points | Yes | Yes |
| `SOL FIXA` | Vector potential / flux linkage | Yes | Yes |
| `SOL FORC` | Element surface force | Yes | No |
| `SOL FORT` | Maxwell stress tensor force | Yes | No |
| `SOL FIXB` | Lorentz force on coils | Yes | No |
| `SOL MAS` | Charge file output (for BEAM) | Yes | No |
| `SOL FMAG` | Center field (MJH elements) | Yes | No |

**Key constraint:** SOL MOME or SOL MOMC must execute first. Choose one (not both).
After SOL MOMC, only SOL FIEL and SOL FIXA are available.

## ELFIN SOL Types
Same structure: SOL MOME (mandatory), then SOL FIEL, SOL FORC, SOL FORT, SOL MAS.

## BEAM SOL Type
Only `SOL BEAM` (trajectory computation).

## Common Sub-Keywords

### SOL MOME / SOL MOMC
| Keyword | Description | Example |
|---------|-------------|---------|
| `TIME` | Time stepping (MAXSTEP, a, b; dt=a/b) | `TIME 20 0.001 1.0` |
| `NONL` | Nonlinear convergence (N, eps, old) | `NONL -3 0.01` |
| `DMEG` | Load geometry + write results to .meg | `DMEG` |
| `BLAS` | Matrix precision (8=double, 4=single) | `BLAS 8` |
| `NCPU` | Parallel threads (0=auto) | `NCPU 0` |
| `NOGO` | Dry run (check input only) | `NOGO` |
| `EMFM` | Induced current (MID, NB3) | `EMFM 1 4` |
| `STAR` | Star/neutral connection | `STAR 1 2 3` |
| `HOLE` | Zero resistance near axis | `HOLE 0.001 3` |
| `PASS GENE` | Skip matrix assembly (reuse .mat) | `PASS GENE` |
| `PASS STEP ALL` | Skip MOME, compute post-blocks only | `PASS STEP ALL` |
| `PASS SW` | Speed optimization (0/1/2) | `PASS 2` |
| `HBGO` | Ignore B-H curve defects | `HBGO` |
| `EMGO` | Force induced current with current input | `EMGO` |
| `CLGO` | Force unbalanced coil subdivision | `CLGO` |
| `MACH` | DC superposition (2-pass) | `MACH problem1` |
| `FREQ` | Frequency [Hz] (MOMC only) | `FREQ 0 1000` |

### NONL Convergence Strategy
```
NONL  -3  0.01        # Newton-Raphson: 3 iterations (fast approach)
NONL   3  0.01        # Iterative correction: 3 iter (true solution)
NONL  -3  0.01        # NR again
NONL  10  0.01        # Iterative: 10 iter (final convergence)
```
- N > 0: successive substitution (if converges = true solution)
- N < 0: Newton-Raphson (fewer iterations but approximate)
- **Recommended:** alternate NR and iterative, finish with iterative
- `old` parameter (0 to <1): stabilization for non-converging iterative steps

### PASS Speed Optimization
| PASS | Matrix | LU | Use Case |
|------|--------|----|----------|
| (auto) | auto | auto | Default -- use normally |
| 0 | rebuild | rebuild | Full rebuild (baseline) |
| 1 | skip | rebuild | Nonlinear B-H with motion |
| 2 | skip | skip | Linear B-H (fastest) |

Validate PASS 1/2 results against PASS 0 for a few steps.

### SOL FIEL
| Keyword | Description |
|---------|-------------|
| `TIME` | Step selection (STEP1, STEP2, STEP3); supports `LAST`, `LAST-N` |
| `DMEG` | Read space nodes/MCO elements |
| `ELEM` | Compute surface field on poly elements |

### SOL FORC / SOL FORT
| Keyword | Description |
|---------|-------------|
| `SEL1` | Select single element face |
| `SELE` | Select by element range |
| `SELM` | Select by material range |
| `SELP` | Select poly elements |
| `DELE/DELM/DELP` | Deselect duplicate faces |
| `PART` | Face subdivision for accuracy |

### SOL FIXB (Lorentz Force on Coils)
| Keyword | Description |
|---------|-------------|
| `COIE` | Select coil by element (EID, NB3) |
| `COIM` | Select coil by material (MID, NB3) |

### SOL FIXA (Flux Linkage)
| Keyword | Description |
|---------|-------------|
| `FLUM` | Flux linkage target (MIDT, NB3, MIDS) |
| `DMEG` | Read flux line drawing elements |

FLUM with MIDT=MIDS: self-inductance. Different: mutual inductance.

### SOL BEAM
| Keyword | Description |
|---------|-------------|
| `STEP` | Max tracking steps |
| `TIME` | Time step size [s] |
| `STOP XYZ` | Bounding box [m] |
| `STOP ELEM` | Beam stop surface elements |
| `BMEG` | Read beam stop meg file |
| `DMEG` | Read particle file |
| `OMAG` | Output data thinning |
| `RELA` | Relativistic correction |
| `RUNG` | Solver method (1=Euler, 4=RK4) |
| `BINT` | Beam-beam interaction (space charge) |
| `GRAV` | Gravitational acceleration |
"""

# ============================================================
# .mei format
# ============================================================

MEI_FORMAT = """\
# .mei File Format (Mesh Script)

The `.mei` file is a **procedural mesh scripting language** processed by
IEmesh (mesh750.exe) to generate .meg files. It is NOT raw mesh data.

## Structure

```
MODEL <SOLVER> <SYMMETRY>    # Header (MAGIC/ELFIN/BEAM + T/K/R)
GSC <scale>                  # Global scale (e.g., 0.001 for mm->m)
IMA X                        # Image symmetry plane(s)
PUT A=10.0                   # Variable assignment

<source region commands>     # Coils, magnets, conductors, dielectrics

SPACE                        # Separator

<evaluation region commands> # Field evaluation surfaces (MCO/ECO)

STOP                         # End of script
```

## Variable Assignment
```
PUT A=10.0
PUT B=A*2.0
PUT C=_COS(30.0)*A         # Functions: _COS, _SIN, _TAN, _SQRT, _ABS, ...
```

## Two Regions
1. **Before SPACE**: Source geometry (material nodes MGR1/EGR1 + elements)
2. **After SPACE**: Evaluation geometry (space nodes MGR2/EGR2 + MCO/ECO elements)

## Comments
- `*` at line start
- `#` or `!` anywhere to end of line
- `{` / `}` block comments
- `==` at line start = end of data

## Control Flow
- `LOOP var = start end step` / `LOOPEND` (nest up to 10 levels)
- `IF (condition)` / `ELSE` / `ENDIF`
- `CASEIF var` / `CASE v1` / `CASEELSE` / `CASEEND`
- `GOTO label$` / `GOAL label$`

## Subroutines
```
SUBR name$(var1 var2)
  ...
RETURN

CALL name$(v1 v2)
```

## Configuration
- `INIT ELEM MAX` -- max node/element number (default 200000)
- `DEF EPS eps` -- merge tolerance (default 1E-10)
"""

# ============================================================
# .mei commands
# ============================================================

MEI_COMMANDS = """\
# Mesh Scripting Commands (.mei)

## AA -- Direct Element Creation (Auto-Mesh)

| Command | Shape | Description |
|---------|-------|-------------|
| `AA(O,x,y,z)` | -- | Set origin for next AA |
| `AA(N,N1)` | -- | Set origin by node |
| `AA(P,AX$)` | -- | Change coordinate axes (XY,XZ,YZ,...) |
| `AA(B,M1,M2,M3)` | -- | Set default division counts |
| `AA(LINEX,lx,Mx)` | Line | X-direction line |
| `AA(LINEY,ly,My)` | Line | Y-direction line |
| `AA(RECT,lx,ly,Mx,My)` | Quad | Rectangle |
| `AA(BLOCK,lx,ly,lz,Mx,My,Mz)` | Hex | Rectangular solid |
| `AA(BOX,lx,ly,lz,Mx,My,Mz)` | Quad | Box surface (6 faces) |
| `AA(BOX1,lx,ly,Mx,My)` | Line | Rectangle outline |
| `AA(ARCH3,rs,rl,t1,t2,lz,Mr,Mt,Mz)` | Hex | Arch/torus sector |
| `AA(ARCH2,rs,rl,t1,t2,Mr,Mt)` | Quad | Arch surface |
| `AA(ARCH1,r,t1,t2,Mt)` | Line | Arch line |
| `AA(RING1,r,Mt)` | Line | Ring (line) |
| `AA(RINGB,rs,rl,lz,Mt)` | Hex | Ring solid |
| `AA(SQRING,lx,ly,lz,lt,r,Mr)` | Hex | Square ring (coil) |
| `AA(SPHSUR,r,M)` | Tri | Sphere surface (20*M*M triangles) |
| `AA(CYLSUR,r,lz,Mr,Mt,Mz)` | Quad | Cylinder surface |
| `AA(CYLSOL,r,lz,Mr,Mt,Mz)` | Hex | Cylinder solid |
| `AA(DISK,r,Mr,Mt)` | Quad | Disk surface |
| `AA(HELICAL,r,Mt,zp,K,L)` | Line | Helix (K turns, L layers) |
| `AA(HOLE,En,r,t,Mr,M1,M2)` | Quad | Punch hole in quad |

## AN -- Node Creation

| Command | Description |
|---------|-------------|
| `AN(XYZ,x,y,z)` | Cartesian |
| `AN(RT2,r,t)` | Polar (2D) |
| `AN(RT3,r,t,z)` | Cylindrical |
| `AN(F3,N1,...,N2)` | Equal-division on line |
| `AN(FL,N1,N2,ND,p)` | Ratio-division on line |
| `AN(FC,NC,N1,N2,ND,p)` | Ratio-division on arc |
| `AN(PL,N1,N2,M,p)` | Equal-ratio by count |
| `AN(PC,NC,N1,N2,M,p)` | Arc by count |
| `AN(PB,N1,N2,N3,N4,M1,M2)` | Grid on quadrilateral |
| `AN(LLX,N1,N2,N3,N4)` | Line-line intersection |
| `AN(CNW,N1,N2,N3)` | Circle through 3 points |

## AE -- Element Creation by Node

| Command | Description |
|---------|-------------|
| `AE(N1,N1)` | Point element |
| `AE(N2,N1,N2)` | Line (2 nodes) |
| `AE(N3,N1,N2,N3)` | Triangle |
| `AE(N4,N1,N2,N3,N4)` | Quad |
| `AE(N6,N1,...,N6)` | Triangular prism |
| `AE(N8,N1,...,N8)` | Hexahedron |
| `AE(NP,SW,N1,...,Nn)` | 2D poly element |

## NB -- Material/Name Assignment

| Command | Description |
|---------|-------------|
| `NB(NAME,xxx)` | Set element label (MWL, MCL, MMB, etc.) |
| `NB(MID,n)` | Set material ID |
| `NB(PID,n)` | Set poly ID |
| `NB(CHAN,MM,old,new)` | Change material ID |
| `NB(CHAN,NM,name,mid)` | Rename by name |

## SE/SN -- Selection

| Command | Description |
|---------|-------------|
| `SE(ADD,ALL)` | Select all elements |
| `SE(ADD,E1,E2)` | Select element range |
| `SE(ADD,M,M1,M2)` | Select by material |
| `SN(ADD,ALL)` | Select all nodes |

## ME -- Mesh Operations

| Command | Description |
|---------|-------------|
| `ME(CPL,d,K)` | Copy elements (linear, K copies) |
| `ME(CPC,t,K)` | Copy elements (rotational) |
| `ME(CPM,SW)` | Copy elements (mirror) |
| `ME(EXL,d,M)` | Extrude linear (surface -> solid) |
| `ME(EXC,t,M)` | Extrude rotational |
| `ME(MVL,d)` | Move linear |
| `ME(MVC,t)` | Move rotational |
| `ME(DEL)` | Delete selected |
| `ME(B2S,Pn,Mn)` | Solid to surface conversion |

## BE -- Element Division

| Command | Description |
|---------|-------------|
| `BE(L2,M,p)` | Divide line |
| `BE(L4,M1,M2,p1,p2)` | Divide quad |
| `BE(L8,M1,M2,M3)` | Divide hexahedron |
| `BE(H4,SW)` | Quad to 2 triangles |

## TE -- Element Direction

| Command | Description |
|---------|-------------|
| `TE(REV)` | Reverse element direction |
| `TE(WLV)` | Align magnet to vector |
| `TE(WLR,SW)` | Align magnet radially |
| `TE(CLV)` | Align coil around vector (right-hand rule) |
| `TE(CME,En)` | Align normals by reference element |
| `TE(TRI)` | Convert quad to triangle |

## Other

| Command | Description |
|---------|-------------|
| `RB(MERGE,eps)` | Merge coincident nodes |
| `RB(EN)` | Renumber elements and nodes |
| `RB(STORE)` | Store current data |
| `CL(LONE)` | Clean orphan nodes |
| `VECX x1 y1 z1 x2 y2 z2` | Define direction vector |
| `VECN N1 N2` | Direction by nodes |
| `GE(N2,P)` | Geometric division ratio |
| `DMEG file.meg 1` | Import meg data |
"""

# ============================================================
# .meg format
# ============================================================

MEG_FORMAT = """\
# .meg File Format (Compiled Mesh Data)

The `.meg` file is fixed-format text output from IEmesh, containing node
coordinates and element connectivity.

## Generation routes

- Standard ELF route: author `.mei`, then compile it with IEmesh/mesh750.exe
  to produce `.meg`.
- Cubit route: `cubit_mesh_export` can emit ELF-compatible `.meg` meshes when a
  larger CAD/mesh workflow is useful. Common helper calls are
  `cubit_mesh_export.export_meg(cubit, "model.meg", DIM="T")` and
  `cubit_mesh_export.export_3D_meg(cubit, "model")`; command-style
  `radia_export meg ...` workflows may wrap the same idea.
- Public sample corpus route: the bundled public `.mai`/`.meg` examples use
  small lab-authored ASCII `.meg` writers that emit `BOOK MEP 3.50`, `MGSC`,
  `MGR1` node records, and element connectivity directly. Cubit is not used
  for those compact public examples.

## Structure

```
BOOK  MEP  3.50                    # Header
* ELF/MESH VERSION 5.3.7          # Version comment
MGSC 0.001                        # Scale (M=MAGIC, E=ELFIN, B=BEAM)
MIMA -X                           # Symmetry

MGR1  1  0  x  y  z               # Source nodes
<element records>                  # Source elements

MGR2  1  0  x  y  z               # Evaluation nodes
<element records>                  # Evaluation elements

BOOK  END                          # Footer
```

**Max line length: 120 half-width characters.**

## Scale Headers
- `MGSC <scale>` -- MAGIC coordinate multiplier to meters
- `EGSC <scale>` -- ELFIN
- `BGSC <scale>` -- BEAM

## Symmetry Headers
- `MIMA X` / `MIMA -X` -- same/opposite-pole mirror about YZ plane
- `MIMA ZC <N>` -- N-fold periodic rotational symmetry
- `MIMA -ZC <N>` -- opposite-pole periodic (N must be even)
- `EIMA` / `BIMA` -- same for ELFIN/BEAM

### Symmetry Availability
| Type | X | Y | Z | ZC |
|------|---|---|---|----|
| T (3D) | Yes | Yes | Yes | Yes |
| R (Axisym) | No | No | Yes | No |
| K (2D) | Yes | Yes | No | No |

### Force/Torque Multipliers for Symmetry
| MIMA | Fx | Fy | Fz | Tx | Ty | Tz |
|------|----|----|----|----|----|----|
| +/-X | 0 | 2 | 2 | 2 | 0 | 0 |
| +/-Y | 2 | 0 | 2 | 0 | 2 | 0 |
| +/-Z | 2 | 2 | 0 | 0 | 0 | 2 |
| +/-ZC n | 0 | 0 | n | 0 | 0 | n |

Multiply across all active symmetries. Zero means that component cancels.

## Periodic Boundary Conduction
`MLIN <eps>` -- eddy currents conduct across periodic boundary (normally insulated).

## Node Records
```
MGR1  <id>  0  <x>  <y>  <z>     # Source node
MGR2  <id>  0  <x>  <y>  <z>     # Evaluation node
```

## Element Records
```
<TYPE>  <id>  0|<PID>  <MID>  <n1>  <n2>  [<n3> ... <n8>]
```

Element TYPE = **PREFIX(2-3 chars) + NODECOUNT(1 digit) + DIM(1 char)**
"""

# ============================================================
# Element types
# ============================================================

ELEMENT_TYPES = """\
# ELF Element Type Naming Convention

Element names: **1st char (solver) + 2nd-3rd chars (type) + 4th char (nodes) + 5th char (DIM)**

## DIM Suffix
| Suffix | Symmetry | Description |
|--------|----------|-------------|
| `T` | 3D | Full three-dimensional |
| `K` | 2D | Infinite in Z, XY cross-section |
| `R` | Axisymmetric | Revolution about Z, XZ cross-section |

## Node Count and Shape
| Nodes | Shape |
|-------|-------|
| 8 | Hexahedron (solid) |
| 6 | Triangular prism (solid) |
| 4 | Quadrilateral (surface) |
| 3 | Triangle (surface) |
| 2 | Line segment |
| 1 | Point |

## MAGIC Element Prefixes

### Magnetic Body (soft magnetic, B-H curve in 1st quadrant)
| Prefix | Description | DOF (3D) | Notes |
|--------|-------------|----------|-------|
| `MMB` | General magnetic body | 6(hex),5(prism) | **Recommended** |
| `MMS` | Thick plate (no top/bottom charge) | 4,3 | MMB preferred |
| `MMT` | Thin plate (edge charge) | 1 | MMB preferred (v4.00+) |
| `MMP` | Poly element (closed polyhedra) | 1 | For arbitrary shapes |

### Magnet (permanent magnet, B-H in 2nd/3rd quadrant)
| Prefix | Description | DOF | Notes |
|--------|-------------|-----|-------|
| `MWL` | Direction by element (bottom=S, top=N) | 1 | |
| `MWV` | Direction by VEC1/VEC3 vector | 1 | **Recommended** |

### Coil (current-carrying)
| Prefix | Description | DOF | Notes |
|--------|-------------|-----|-------|
| `MCL` | Coil element | 0 | Direction = node order |

### Eddy Current
| Prefix | Description | DOF (3D) | Notes |
|--------|-------------|----------|-------|
| `MAB` | Non-magnetic conductor | 6,5 | Adjacent = conducts |
| `MAT` | Non-magnetic thin plate | 1 | |
| `MBB` | Magnetic conductor | 12,10 | B-H + eddy current |

**Holes in eddy current bodies:** Fill with high-resistivity MAB (target ~1 ohm*m).

### Evaluation / Other
| Prefix | Description | DOF | Notes |
|--------|-------------|-----|-------|
| `MCO` | Contour (field evaluation) | 0 | Space nodes, SOL FIEL |
| `MCM` | Maxwell stress evaluation | 0 | Space nodes, SOL FORT |
| `MJH` | Center field | 0 | Material nodes, SOL FMAG |
| `MCB` | Beam stop surface | 0 | 3D only |
| `M..` | Shape (display only) | 0 | No computation |

## ELFIN Element Prefixes

| Prefix | Description | DOF |
|--------|-------------|-----|
| `EMB` | Dielectric body | 6,5,4,3 |
| `EMS` | Dielectric thick plate | 4,3 |
| `EMT` | Dielectric thin plate | 1 |
| `EMP` | Dielectric poly | 1 |
| `ESC` | Electrode (known potential) | 1 |
| `EQL` | Fixed charge | 0 |
| `ESH` | Boundary (permittivity ratio) | 1 |
| `ESS` | Boundary (normal E both sides) | 1 |
| `ESN` | Boundary (normal E front side) | 1 |
| `ECO` | Space field evaluation | 0 |
| `ECM` | Maxwell stress evaluation | 0 |
| `ECB` | Beam stop surface | 0 |

## BEAM Element Prefixes
| Prefix | Description |
|--------|-------------|
| `BGR1` | Particle initial position |
| `BGR2` | Particle velocity direction |

## Label Availability by DIM

### T (3D): MMB MMS MMT MMP MWL MWV MCL MAB MAT MBB MCO MCM MJH MCB
### K (2D): MMB MMT MMP MWL MWV MCL MAB MAT MBB MCO MCM MJH
### R (Axisym): MMB MMT MMP MWL MWV MCL MAB MAT MBB MCO MCM

(3D adds MMS, MCB; 3D adds MJH for K; R has no MJH)
"""

# ============================================================
# B-H Curves
# ============================================================

BH_CURVES = """\
# B-H Curve Specification in ELF

## Unit Declaration
```
HBUN  <curve_id>  <unit_system>
```
- `OE/G` or just `OE` -- Oersted/Gauss (CGS)
- `A/M/T` or just `A/M` -- A/m and Tesla (SI)

## Scale Factors
```
HBSC  <curve_id>  <H_scale>  <B_scale>
```

## Curve Data Points
```
HBCU  <curve_id>  <H_value>  <B_value>
```
- Minimum 2 points, max 100 per curve
- Must be monotonically increasing in H
- **Magnetic bodies:** start from origin (0,0), 1st quadrant only
- **Magnets:** start from negative H (2nd/3rd quadrant), can extend to 1st

**Extrapolation warning:** If solution H exceeds max input H, extrapolates
from last 2 points. If slope >> mu_0, moment becomes excessive. Use
MaiEditor3 auto-extension to add safe extrapolation points.

## Curve Copy
```
HBEQ  <dest_id>  <source_id>        # Note: dest first
HBCP  <source_id>  <dest1> <dest2>  # Note: source first
```

## Curve-to-Material Assignment (per timestep)
```
HBCN  <MID>  <STEP>  <curve_id>
```
Different B-H per step enables demagnetization analysis.

## Recoil Permeability (Demagnetization)
```
HBRM  <curve_id>  <recoil_slope>  <Bmax>
```
- Bmax = max residual magnetization for irreversible process
- Knee point = intersection of recoil line through Bmax with B-H curve
- Below knee point: irreversible demagnetization occurs

## Example (Silicon steel in SI)
```
HBUN  1  A/M  T
HBCU  1      0.0    0.0
HBCU  1    200.0    1.0
HBCU  1    500.0    1.4
HBCU  1   5000.0    1.8
HBCU  1  50000.0    2.0
```

## Example (NdFeB magnet, Br=1.35T, Z-direction)
```
HBUN  1  A/M  T
HBCU  1  -700000.0  0.0
HBCU  1       0.0   0.90
```
Direction set by VEC1/VEC3 for MWV elements, or by element node order for MWL.
"""

# ============================================================
# MAGIC solver
# ============================================================

MAGIC_DOCS = """\
# MAGIC Solver (Magnetostatic BEM)

MAGIC solves magnetostatic field problems using the integral element method
(moment method / BEM). Supports static, transient, and sinusoidal analysis.

## Analysis Types

| Type | TIME | Elements | NONL | Description |
|------|------|----------|------|-------------|
| Single static | STEP=0 | MB,WL,CL | Yes | Basic magnetostatic |
| Multiple static | STEP>0 | MB,WL,CL (no AB/BB) | Yes | Batch parameter sweep |
| Transient | STEP>0 | MB,WL,CL,AB,AT,BB | Yes | Eddy current + motion |
| Sinusoidal (MOMC) | STEP>=0 | All | No | AC/frequency domain |

## Typical .mai Structure
```
USE  MAGIC  3.50
PRE
  HBUN 1 A/M T
  HBCU 1 0.0 0.0
  HBCU 1 200.0 1.0
  ...
  COI1 1 0 100 8 4 A
  AMP1 1 0 5.0
END
SOL MOME
  NCPU 0
  TIME 0 1 1              # Static (STEP=0)
  NONL -3 0.01
  NONL 10 0.01
  DMEG
END
SOL FIEL
  TIME 0
  DMEG
END
```

## Solver Chain
1. `SOL MOME` -- BEM matrix solve (mandatory first)
2. `SOL FIEL` -- B,H at evaluation points
3. `SOL FORC` -- Force on element surfaces (approximate)
4. `SOL FORT` -- Maxwell stress force (**more accurate** than FORC)
5. `SOL FIXB` -- Lorentz force on coils
6. `SOL FIXA` -- Flux linkage, vector potential
7. `SOL MAS` -- Charge file for BEAM
8. `SOL FMAG` -- Center field at MJH elements

## Eddy Current in MAGIC
- Use MAB/MAT (non-magnetic) or MBB (magnetic) elements
- Eddy currents are **automatic** when field varies with TIME steps
- No special header needed -- just include TIME steps and eddy current elements
- Adjacent elements with shared nodes: current conducts
- Double nodes or gaps: current insulated

## Example Categories
| Directory | DIM | Description |
|-----------|-----|-------------|
| MK/ | K (axisym) | Solenoids, pot magnets |
| MR/ | R (2D) | C-core, relay, actuator |
| MT/ | T (3D) | Complex 3D geometry |
| IPM/ | T | Interior permanent magnet motors |
| LscLl/ | K,T | Inductance computation |
| MOMC/ | T | AC complex analysis |
| magne/ | -- | Magnetization/demagnetization |
"""

# ============================================================
# ELFIN solver (electrostatic)
# ============================================================

ELFIN_DOCS = """\
# ELFIN Solver (Electrostatic BEM)

ELFIN solves **electrostatic** field problems using the integral element method.
It is the electric-field counterpart to MAGIC (magnetic field).

## Key Differences from MAGIC

| Feature | ELFIN | MAGIC |
|---------|-------|-------|
| Physical quantity | E, V, D | H, B |
| Material curve | D-E curve (EDSC/EDCU) | B-H curve (HBUN/HBCU) |
| Potential | VOL1 (electrode V) | -- |
| Charge | CHA1 (density), CHA2 (total/floating) | -- |
| Boundary | ESH (eps ratio), ESS/ESN (E normal) | -- |
| Element prefix | E (EMB, ESC, EQL, ...) | M (MMB, MCL, MWL, ...) |
| USE declaration | `USE ELFIN 3.50` | `USE MAGIC 3.50` |

## Applications
- Capacitor design
- High-voltage insulator analysis
- Electrode potential distribution
- Electrostatic force computation
- Electric field shielding

## Element Types
- **EMB** -- Dielectric body (D-E curve, 1st quadrant)
- **ESC** -- Electrode with known potential (VOL1)
- **EQL** -- Fixed charge element (CHA1)
- **ESH** -- Permittivity ratio boundary
- **ESS/ESN** -- Normal E-field boundary
- **ECO** -- Space field evaluation
- **ECM** -- Maxwell stress evaluation

## Typical .mai Structure
```
USE  ELFIN  3.50
PRE
  EDSC 1 1.0 1.0            # D-E curve scale
  EDCU 1 0.0 0.0            # D-E data points
  EDCU 1 1000.0 5000.0
  VOL1 1 0 100.0            # Electrode 1: +100V
  VOL1 2 0 -100.0           # Electrode 2: -100V
END
SOL MOME
  NCPU 0
  NONL -3 0.01
  NONL 10 0.01
  DMEG
END
SOL FIEL
  TIME 0
  DMEG
END
```

## D-E Curve Notes
- D* = epsilon* x E (dimensionless permittivity ratio)
- Monotonically increasing, minimum 2 points
- **CHA2** creates floating electrode: solver finds unknown potential and charge distribution

## Example Categories
| Directory | DIM | Description |
|-----------|-----|-------------|
| EK/ | K (axisym) | Axisymmetric electrostatic |
| ER/ | R (2D) | 2D cross-section |
| ET/ | T (3D) | Full 3D electrostatic |
"""

# ============================================================
# BEAM solver
# ============================================================

BEAM_DOCS = """\
# BEAM Solver (Charged Particle Tracking)

BEAM tracks charged particles through electromagnetic fields computed by
MAGIC and/or ELFIN via .mas charge files.

## Workflow
1. Run MAGIC with SOL MAS -> magnetic .mas file
2. Run ELFIN with SOL MAS -> electric .mas file (optional)
3. Create particle .meg file (BGR1 positions + BGR2 directions)
4. Create .mai with FILE, particle properties, SOL BEAM
5. Run BEAM -> trajectory .mag file

**2D model .mas files cannot be used** -- only 3D and axisymmetric.

## Particle File (.meg)
```
BOOK MEP 3.50
BGSC 0.001
BGR1  1  0  x  y  z       # Particle 1 position
BGR2  1  0  vx vy vz      # Particle 1 velocity direction
BGR1  2  0  x  y  z       # Particle 2 position
BGR2  2  0  vx vy vz
BOOK END
```

## .mai Structure
```
USE  BEAM  3.50
PRE
  FILE  MAGIC  problem_M   # Import magnetic field
  FILE  ELFIN  problem_E   # Import electric field (optional)
  CHAR  1  1.602E-19       # Electron charge [C]
  MASS  1  9.109E-31       # Electron mass [kg]
  VOLB  1  10000.0         # Acceleration voltage [V]
END
SOL BEAM
  STEP  1000               # Max tracking steps
  TIME  1.0E-10            # Time step [s]
  STOP XYZ -0.1 -0.1 0.0 0.1 0.1 0.5   # Bounding box [m]
  RELA                     # Relativistic correction
  DMEG
END
```

## Advanced Features
- **RELA** -- Special relativity (longitudinal + transverse mass)
- **BINT** -- Beam-beam interaction (space charge via line charges + iteration)
- **STOP ELEM** -- Beam stop surfaces (ECB4T/ECB3T) with reflection
- **GRAV** -- Gravitational acceleration
- **RUNG 4** -- 4th-order Runge-Kutta (default: proprietary high-speed method)
- **BIMA** -- Symmetry for beam-beam interaction trajectories

## Example Categories
| Example | Description |
|---------|-------------|
| BX01-BX08 | Various electron optics |
| BX*m | Modified versions |
| BX*e | Extended versions |
| BECB | Beam in ELFIN field |
"""

# ============================================================
# Treasure Box (quick reference tables)
# ============================================================

TREASURE_BOX = """\
# ELF Treasure Box (Quick Reference Tables)

## 1. Element-to-PRE Property Mapping

Which PRE headers apply to which element types:

| Property | Header | MB | MS | MT | MP | WL | WV | CL | AB | AT | BB |
|----------|--------|----|----|----|----|----|----|----|----|----|----|
| B-H curve | HBUN/HBCU | Req | Req | Req | Req | Req | Req | -- | -- | -- | Req |
| B-H copy | HBEQ | Opt | Opt | Opt | Opt | Opt | Opt | -- | -- | -- | Opt |
| Anisotropy | HBA1 | Opt | Opt | Opt | -- | -- | -- | -- | -- | -- | Opt |
| Lamination | HBA2 | Opt | Opt | Opt | -- | -- | -- | -- | -- | -- | Opt |
| Direction | VEC1/VEC3 | Opt | Opt | Opt | -- | -- | Req | -- | -- | -- | Opt |
| Complex mu | CMU1/I | Req* | Req* | Req* | Req* | Req* | Req* | -- | -- | -- | Req* |
| Turns | COI1 | -- | -- | -- | -- | -- | -- | Req | -- | -- | -- |
| Current | AMP1 | -- | -- | -- | -- | -- | -- | Sel | -- | -- | -- |
| Voltage | VOL1 | -- | -- | -- | -- | -- | -- | Sel | -- | -- | -- |
| Resistance | OHM1 | -- | -- | -- | -- | -- | -- | Sel | -- | -- | -- |
| Resistivity | OHM2 | -- | -- | -- | -- | -- | -- | -- | Req | Req | Req |
| Thickness | THIN | -- | -- | Req | -- | -- | -- | Opt | -- | Req | -- |
| Motion | MOV1/ORI1 | Opt | Opt | Opt | Opt | Opt | Opt | Opt | Opt | Opt | Opt |

Req = Required, Opt = Optional, Sel = Selectively required, * = MOMC only

## 2. Calculation Mode Compatibility

| Mode | MOME/MOMC | TIME | MB | WL | CL | AB/AT | BB | EMFM | NONL |
|------|-----------|------|----|----|----|-------|----|----|------|
| Single static | MOME | n=0 | OK | OK | OK | -- | tri | -- | Yes |
| Multiple static | MOME | n>0 | OK | OK | OK | X | X | X | Yes |
| Transient | MOME | n>0 | OK | OK | OK | OK | OK | Opt | Yes |
| Single sinusoidal | MOMC | n=0 | OK | OK | OK | OK | OK | Opt | No |
| Multiple sinusoidal | MOMC | n>0 | OK | OK | OK | OK | OK | Opt | No |

X = cannot use, tri = usable but pointless

## 3. SOL Block Execution Order

| After | FIEL | FORC | FORT | FIXB | FIXA | MAS | FMAG |
|-------|------|------|------|------|------|-----|------|
| MOME | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| MOMC | Yes | No | No | No | Yes | No | No |

## 4. Common Mistakes (Knotty Sample)

| # | Task | Required Elements | Required Settings |
|---|------|------------------|------------------|
| 1 | Eddy current | AB/AT/BB elements | TIME steps (automatic) |
| 2 | Joule heat | AB/AT/BB elements | TIME steps (automatic) |
| 3 | Induced current | CL elements | EMFM + OHM1 + TIME |
| 4 | Flux linkage | CL elements | SOL FIXA + FLUM |
| 5 | Vector potential | Space nodes | SOL FIXA + DMEG |
| 6 | Force on coils | CL elements | SOL FIXB + COIE/COIM |
| 7 | Force on iron | Non-CL elements | SOL FORC + SEL* |
| 8 | Maxwell stress | MCM elements | SOL FORT + SEL* |
| 9 | Plate thickness | MMT/MAT elements | THIN in PRE |

## 5. Current-Direction Subdivision (NB3)

EMFM, FLUM, COIE/COIM all have NB3 parameter (default 4) for subdividing
the coil element along the current direction. Increase when B varies
significantly along a single coil element's length. This is separate from
cross-section subdivision (NB1 x NB2).
"""

# ============================================================
# Sinusoidal Response (SOL MOMC)
# ============================================================

SINUSOIDAL_RESPONSE = """\
# Sinusoidal Response Analysis (SOL MOMC)

SOL MOMC replaces d/dt with jw for frequency-domain (complex linear) analysis.
Results are complex numbers convertible to amplitude and phase.

## Key Points
- **Nonlinear B-H NOT supported** -- use complex permeability (CMU1/CMU1I) instead
- Current/voltage/resistance become complex (AMP1I, VOL1I, OHM3I)
- After MOMC, only SOL FIEL and SOL FIXA available (no FORC/FORT/FIXB)
- Multiple frequencies can be swept (FREQ per STEP)

## Force and Joule Heat in AC Fields

Forces and Joule heat are proportional to the **square** of sinusoidal
quantities, so they oscillate at **2x the driving frequency**:

```
F(t) = A * cos(2*omega*t + P) + B
```

MagFilter2 extracts amplitude A, phase P, and center value B.

## ComplexTransfer2 Tool
Converts complex .mag file to pseudo-transient .mag (1 period / N steps)
for Wmap3 animation:
```
ComplexTransfer.EXE problem.mag 36
```

## Frequency Sweep Example
```
USE MAGIC 3.50
PRE
  CMU1  1 0 100.0           # Real permeability
  CMU1I 1 0 -10.0           # Imaginary permeability
  OHM2  2 0 1.0e-7          # Resistivity
  COI1  3 0 100 8 4 A
  AMP1  3 0 5.0             # Current amplitude (real)
  AMP1I 3 0 0.0             # Current amplitude (imag)
END
SOL MOMC
  TIME 3 1 1                # 4 frequencies (steps 0-3)
  FREQ 0 50
  FREQ 1 100
  FREQ 2 500
  FREQ 3 1000
  EMFM 3 4                  # Induced current
  DMEG
END
SOL FIEL
  TIME 0 3
  DMEG
END
```
"""

# ============================================================
# Anisotropy and Lamination
# ============================================================

ANISOTROPY_LAMINATION = """\
# Anisotropy (HBA1) and Lamination (HBA2)

## HBA1 -- Magnetic Susceptibility Anisotropy
```
HBA1  <MID>  <k>     # 0 < k < 1
```
- k = ratio of hard-direction to easy-direction susceptibility
- Easy direction set by VEC1/VEC3
- Hard-direction susceptibility = k x easy-direction susceptibility
- Applies to: MMB*, MBB* (not MMP*). Also MMS*, MMT* for easy-axis only.

## HBA2 -- Lamination Stacking Factor
```
HBA2  <MID>  <p>     # 0 < p < 1
```
- p = stacking factor (lamination fill factor)
- Models air gap magnetic reluctance in laminated steel
- Stacking direction set by VEC1/VEC3
- Applies to: MMB*, MBB* (not MMP*)

## Mutual Exclusion
**HBA1 and HBA2 cannot be used together on the same material.**

## Direction Setting
```
VEC1  <EID>  0  <vx>  <vy>  <vz>   # Per element
VEC3  <MID>  0  <vx>  <vy>  <vz>   # Per material
```

Used for:
1. MWV* magnet magnetization direction
2. HBA1 easy-magnetization direction
3. HBA2 lamination stacking direction

## For MOMC (Sinusoidal)
Same HBA1/HBA2 syntax, but base permeability from CMU1/CMU1I instead of B-H curve.

## Property Directions Summary

| Element | Direction from meg | HBA1 direction | HBA2 direction | Magnet direction |
|---------|-------------------|----------------|----------------|-----------------|
| MMB | -- | VEC1/VEC3 | VEC1/VEC3 | -- |
| MMS | thickness | VEC (in-plane) | NOT recommended | -- |
| MMT | thickness | VEC (in-plane) | NOT recommended | -- |
| MWL | bottom=S, top=N | -- | -- | node order |
| MWV | -- | -- | -- | VEC1/VEC3 |
| MCL | node order | -- | -- | -- |
| MBB | -- | VEC1/VEC3 | VEC1/VEC3 | -- |
"""

# ============================================================
# Steady-State Eddy Current (STED)
# ============================================================

STEADY_STATE_EDDY = """\
# Steady-State Eddy Current Motion (STED)

For rotating metal disks or translating metal plates in static magnetic fields.

```
STED  <MID>  <dx>  <dy>  <dz>  <dt>  <N>
```
- dx, dy, dz = displacement per step [m]
- dt = rotation angle per step [degrees]
- N = element number difference after one step overlap

## Mesh Requirements
1. Regular mesh division in motion direction
2. Element numbers consecutive perpendicular to motion
3. After one step, mesh overlaps exactly with original
4. Element number difference N must be uniform
5. Periodic rotational symmetry compatible
6. For linear motion: mesh must extend to where eddy current decays

## Example (3000 rpm disk, 5-degree mesh pitch)
```
STED 3 0 0 0 5 10
SOL MOME
  TIME 32 5 3000/60*360
  ...
END
```
"""

# ============================================================
# IPM Motor
# ============================================================

IPM_MOTOR = """\
# IPM Motor Analysis with MAGIC

## Ld/Lq Calculation Flow

1. **Run 1** (Motor1.mai): No coil current, rotate rotor -> flux linkage phi1 (magnet only)
2. **Run 2** (Motor2.mai): With sinusoidal coil current, rotate rotor -> phi2 (magnet + current)
3. **Post-processing:** phi3 = phi2 - phi1 (current-only contribution)
4. Fourier transform to extract fundamental d/q components
5. **Ld = phi3d / Id, Lq = phi3q / Iq**

## .model File Format
```
PartsM1 {
  RotAxis    = 0.0, 0.0, 0.0, 3     # Origin + axis (3=Z)
  Params_Rot = 1, 0.0, 60.0, 0.0
}
Calculations {
  TimeSeries = 180, 0.5, 180.0      # Steps, dt (deg), total angle
}
```

## Key Settings
- 3-phase Y-connection: use STAR for neutral point
- Magnets: HBRM with remanence + direction vectors
- Rotor/stator: MMS elements (laminated steel)
- Motion: ORI1 (Z-axis) + MOV1 (angle per step)
- Flux linkage: SOL FIXA with FLUM for each phase
- Torque: SOL FORT with MCM elements around rotor

## Phase Current Setup (MaiEditor3)
- U-phase: AMP1 amplitude, initial phase 225 deg (sin convention)
- V-phase: 105 deg, W-phase: 345 deg (120-degree offsets)

## Alternative LdLq Method
Three-phase-to-two-phase transform (Clarke) -> rotating coordinate transform
(alpha-beta -> d-q). Requires all 3 phase flux linkages.

## Example Files
- `magic/IPM/Motor1.mai` + `Motor1.meg` + `Motor1.model`
- `magic/IPM/Motor2.mai` + `Motor2.meg` + `Motor2.model`
- Excel: `LdLqの計算.xlsx` (Fourier), `LdLqの計算_座標変換.xlsx` (transform)
"""

# ============================================================
# Motor bridge: radia-mcp concepts -> ELF/MAGIC workflows
# ============================================================

MOTOR_RADIA_BRIDGE = """\
# Motor Workflows: radia-mcp Concepts -> ELF/MAGIC

This topic is a practical translation table for rotating-machine studies.
Use it after `ipm_motor` when you want to turn open motor-FEA concepts
(air-gap field, torque, flux linkage, skew, lamination/core loss) into
ELF/MAGIC input files and post-processing steps.

## Concept Map

| Motor quantity | radia-mcp / open-FEA concept | ELF/MAGIC representation |
|----------------|------------------------------|--------------------------|
| Open-circuit PM air-gap field | PM source sweep, read B_r(theta) | MWL/MWV magnet elements + MCO/MJH space points + `SOL FIEL` |
| Iron-boosted PM field | Add stator/rotor iron reluctivity | MMB/MMP/MMS/MBB iron elements + B-H curve or linear high-mu curve |
| Cogging / reluctance torque | Maxwell-stress air-gap torque vs angle | MCM closed stress surface around rotor + `SOL FORT` |
| Lorentz coil force | J x B force on windings | MCL coil elements + `SOL FIXB` |
| Flux linkage / back-EMF | Phi(theta), e = -dPhi/dt | MCL search/phase coils + `SOL FIXA` / FLUM, then differentiate |
| Ld/Lq | PM-only and current-on flux sweeps | `Motor1`/`Motor2` IPM workflow, then Fourier or dq transform |
| Rotor rotation sweep | Rotate mesh or magnetization angle | `ORI1` + `MOV1`, `.model` rotor settings, and TIME steps |
| Laminated steel | Effective anisotropic reluctivity | `HBA2` stacking factor + `VEC1`/`VEC3` stacking direction |
| Eddy-current rotor/shield | Time-domain or sinusoidal diffusion | MAB/MAT/MBB + `TIME`, `STED`, or `SOL MOMC` |

## Minimal Progression for Motor Examples

1. **PM-only rotor field:** Build a magnet ring or IPM magnet set, place
   `MCO*` / `MJH*` evaluation points in the air gap, run `SOL MOME` then
   `SOL FIEL`, and Fourier-analyse B_r(theta).
2. **Add linear iron:** Add stator/rotor iron with a simple monotone B-H
   table or high-mu linear curve. Keep the same observation points so the
   field boost is a direct ratio.
3. **Torque:** Add an `MCM*` stress surface that encloses the rotor in the
   air gap. Sweep rotor angle with `ORI1`/`MOV1` and run `SOL FORT`.
4. **Flux linkage:** Add phase/search coils (`MCL*`), run `SOL FIXA` with
   FLUM, unwrap Phi(theta), and compute back-EMF from angular speed.
5. **Current-on machine:** Add three-phase `AMP1` definitions, `STAR` when
   needed, and compare magnet-only vs current-on flux for Ld/Lq.
6. **Loss extensions:** Use `HBA2` for lamination direction, `MOMC` for
   linear harmonic studies, and MAB/MAT/MBB with TIME/STED for conducting
   rotor or shield problems.

For robust PM-only pickup examples, vary pickup radius, pickup position,
and rotor angle separately before adding current or iron. Include at least
one sign-changing rotor angle and keep every pickup integration surface
comfortably in air, away from magnet/iron boundaries.

## ELF/MAGIC Details That Matter

- MWL magnets get their magnetisation direction from element winding
  (node/face ordering); MWV magnets use `VEC1`/`VEC3`.
- A simple linear soft-iron stator/rotor yoke can be authored as `MMB8T`
  hexahedra with a two-point B-H curve, for example
  `HBUN 2 OE G; HBCU 2 0 0; HBCU 2 1 1000` for an approximate
  `mu_r=1000` material.
- Air-gap probes should not sit numerically on a material boundary. Put
  `MCO*` / `MJH*` points safely inside air when comparing B_r(theta).
- Search or phase coils can be modeled with `MCL8T` volume coils or the
  line-coil family (`MCL2T`/`MCL1*`). Define turns and source type with
  `COI1`; for a passive pickup coil, set its `AMP1` current to zero and
  request `SOL FIXA` / `FLUM` for that coil material.
- `FLUM <MIDT> [NB3] [MIDS]` writes flux-linkage records (`M1MF`) to
  the `.mag` result. Sweep rotor angle, collect Phi(theta), and compute
  back-EMF from `e = -omega dPhi/dtheta`.
- For mutual-flux or pickup-coil studies, keep source and measurement
  coils as separate material IDs. Drive only the source coil with `AMP1`,
  keep the pickup coil passive (`AMP1=0`), and use
  `FLUM <pickup_mid> <nb3> <source_mid>` when you need source-isolated
  linkage rather than total linkage. Check current sign and scaling with
  paired positive/negative-current runs before adding magnets or iron.
- `SOL MOME` is the first solve. Post-blocks (`FIEL`, `FIXA`, `FORT`,
  `FIXB`) read the solved state and can be added incrementally.
- `SOL MOMC` is linear AC only: use `CMU1`/`CMU1I` instead of nonlinear
  B-H curves, and remember that after MOMC only `FIEL` and `FIXA` are
  available.
- For torque, prefer `SOL FORT` with a clean closed stress surface in the
  air gap. `SOL FORC` is useful, but stress-surface torque is usually the
  motor quantity to track.
- For 3D stress integration, place a closed `MCM4T` surface around the
  target rotor/body in the air region, select it with `SELM ON <mid> <mid>
  1`, and read the `.mao` `TOTAL =` row as
  `area flux Fx Fy Fz Tx Ty Tz`.

## Useful Starting Points

- `elf_usage("ipm_motor")`: vendor IPM Ld/Lq workflow and example files.
- `elf_usage("force_methods")`: FORC/FORT/FIXB comparison.
- `elf_usage("anisotropy")`: lamination and anisotropic material setup.
- `elf_usage("sted")`: steady-state eddy-current motion.
- `elf_examples_search("MT06")`: IPM cogging-torque tutorial files.
- `elf_examples_search("Motor1")`: IPM Ld/Lq example files.
"""

# ============================================================
# Inductance computation
# ============================================================

INDUCTANCE_DOCS = """\
# Inductance Computation

## Self-Inductance (Basic)
1. Set linear permeability, 1A current, N turns
2. Run SOL MOME + SOL FIXA with FLUM
3. L = flux_linkage / current

## Two Definitions of Leakage Inductance

### Lsc (JIS Standard) -- Short-Circuit Inductance
Measured by short-circuiting secondary, computing primary impedance:
```
Lsc = X / (2*pi*f)
```
where X = Im(Z), Z = V/I (complex impedance at frequency f).

With zero resistance: Lsc = L1 * (1 - M^2 / (L1 * L2))

### Ll (IEEJ Definition) -- Leakage Inductance
Based on leakage flux energy:
```
Ll = L1 - 2*(n1/n2)*M + (n1/n2)^2 * L2
```
where Le1 = L1 - (n1/n2)*M, Le2 = L2 - (n2/n1)*M, Ll = Le1 + (n1/n2)^2*Le2

Energy method: Set I2 = -(n1/n2)*I1 to cancel main flux, then Ll = 2*W/I1^2

### Comparison
- Ll >= Lsc always; they converge as coupling approaches 1
- Lsc is easily measurable; Ll is theoretical

## 6 Calculation Samples (magic/LscLl/)

| Sample | Method | Description |
|--------|--------|-------------|
| 1 | Lsc | Basic: secondary short-circuit at 50Hz |
| 2 | Lsc | With current distribution (9 parallel sub-coils) |
| 3 | Lsc | Three-phase AC (Y-primary, delta-secondary) |
| 4 | Ll | Field energy method (cancel main flux) |
| 5 | Ll | From L1, L2, M via formula |
| 6 | Lsc | From L1, L2, M (resistance=0) |

## Key Formulas
| Quantity | Formula |
|----------|---------|
| Self-inductance | L = phi / I |
| Mutual inductance | M = phi_12 / I_1 |
| Lsc (JIS) | X / (2*pi*f) |
| Lsc (R=0) | L1 * (1 - M^2/(L1*L2)) |
| Ll (IEEJ) | L1 - 2*(n1/n2)*M + (n1/n2)^2*L2 |
| Ll (energy) | 2*W/I1^2 |
"""

# ============================================================
# Magnetization / demagnetization
# ============================================================

MAGNETIZATION_DOCS = """\
# Magnetization and Demagnetization Analysis

## Demagnetization by Opposing Field (3 steps)
- Step 0: No opposing field (operating point on B-H curve)
- Step 1: Opposing field applied (operating point moves left)
- Step 2: Opposing field removed (returns on recoil line)

If operating point passes knee point: **irreversible demagnetization**.
Recoil remanence ratio = L2/L1.

### ELF Implementation
- `HBRM <curve_id> <recoil_slope> <Bmax>` -- recoil line definition
- `HBCN <MID> <STEP> <curve_id>` -- different B-H per timestep

### Temperature Demagnetization (3 steps)
- Step 0: Normal temperature
- Step 1: Low/high temperature (shifted B-H curve)
- Step 2: Return to normal (inherit remanence ratio)

## Magnetization Analysis (3-Step Workflow)

### Step 1: Magnetizer Calculation
- Model magnet material as MMB (magnetic body) in magnetizer with coil
- Apply strong current -> compute B distribution
- Use initial magnetization curve (1st quadrant B-H)

### Step 2: Extract Magnet Model (MAGNE2.exe)
- Determines residual magnetization from Step 1 results
- Magnetization ratio k from k-H curve
- Converts MMB elements to MWV (magnet) elements
- Creates M.meg (shape) and M.mai (properties)
- Configuration: Step1-2.txt with problem names, CMID, 2nd-quadrant B-H, k-H curve

### Step 3: Magnetic Circuit Evaluation (VEC1C2.exe)
- Import M.meg into magnetic circuit via IEmesh DMEG command
- VEC1C2.exe corrects A.mai with magnetization vectors from M.mai
- Run final ELF/MAGIC calculation

### Multi-Step Extraction (MAGNE2.exe modes)
| Mode | Description |
|------|-------------|
| 1 | Per-element maximum timestep (recommended) |
| 2 | Global maximum timestep |
| 3 | Average maximum timestep |
| 4 | Directly specified timestep |
| 5 | Specified element's maximum timestep |

## Example Files
- `magic/magne/magnetize/CASE1-5` + `Samlpe/`
- `magic/magne/demagne/Sample01-04`
"""

# ============================================================
# Meshing Guidelines
# ============================================================

MESHING_GUIDELINES = """\
# Model Creation and Meshing Guidelines

## Element Shape Quality
- Hexahedra closer to cubes give better accuracy
- Since v4.00, thin/elongated hexahedra have improved accuracy
- **Obliquely crushed shapes degrade accuracy** -- lines connecting opposite
  face centers should be mutually perpendicular
- **Quads better than triangles** -- use triangles only to resolve diagonal issues

## Element Connectivity
- **Matching boundaries** between adjacent elements improve accuracy
- **Unmatched boundary** with face exposed to air: parasitic charges degrade accuracy
- **Gaps** between elements: increased magnetic reluctance -> underestimated moment
- **Overlapping** elements: negative reluctance -> overestimated moment
- **T-junctions** (intermediate nodes): cause insulation for eddy currents
  (acceptable for non-eddy-current analysis)

## Gap Region Meshing
- Face-to-face offset angle theta: **< 45 degrees**
- Element edge length at gap face: **<= gap distance**
- For moving models: mesh alignment at each step matters

## Coil Subdivision
- Solid coil replaced by NB1 x NB2 line currents
- Near-coil spatial field: increase NB1/NB2 so line current pitch <= half
  distance to space node
- Unbalanced NB1:NB2 ratio causes warning (ELF-W 901-903); use CLGO to override

## Eddy Current Element Holes
- Holes must be filled with high-resistivity MAB (target ~1 ohm*m)
- Fill creates equal/opposite currents that cancel, leaving edge current
- Bay-shaped openings connecting to exterior do not need filling

## Poly Elements (MMP)
- One poly = multiple pieces with same MID and PID
- Adjacent poly elements need boundary pieces from each
- Poly center must be inside the closed region; subdivide if not
- Ideal shape: sphere
"""

# ============================================================
# Nonlinear Convergence
# ============================================================

NONLINEAR_CONVERGENCE = """\
# Nonlinear Convergence

## Log File Columns
| Column | Meaning |
|--------|---------|
| ITERATION | Iteration count |
| CONVERGENCE | Maximum element error |
| MU*(NOW) | Relative permeability this iteration |
| MU*(NEXT) | Relative permeability for next |
| KIND | Element type with max error |
| ELEMENT | Element number with max error |
| MID | Material number with max error |

Iterative method lines: `++`, Newton-Raphson lines: `--`

## Convergence Criteria
- **Iterative:** |MU*(NOW) - MU*(NEXT)| / MU*(NOW) <= eps for ALL elements
- **Newton-Raphson:** |Bk - Bk-1| / Bk <= eps

## Troubleshooting Non-Convergence
1. **Increase iterations** -- if error is decreasing, more iterations may suffice
2. **Check mesh quality** -- extreme aspect ratios at max-error element
3. **Smooth B-H curve** -- check XT (differential susceptibility) in log:
   - RXT > 1.0: piecewise-linear is convex downward
   - RXT < 1.0: convex upward
   - Oscillating RXT: convergence is difficult; smooth data points
4. **Use stabilization coefficient** -- `NONL N eps old` with 0 < old < 1
5. **Extend B-H curve** -- `!` in moment output means H exceeded input range;
   extend curve until slope approaches mu_0

## Without NONL
B-H curve treated as **linear** using first 2 points only, even with 3+ points.
"""

# ============================================================
# Force Calculation Methods
# ============================================================

FORCE_METHODS = """\
# Force Calculation Methods

## Comparison

| Method | SOL Block | Elements | Accuracy | Use Case |
|--------|-----------|----------|----------|----------|
| Element surface force | FORC | Material elements | Lower | Quick estimate |
| Maxwell stress | FORT | MCM elements | **Higher** | Accurate force/torque |
| Lorentz force | FIXB | MCL coil elements | Good | Force on coils |

## SOL FORC (Element Surface Force)
- Computes force on selected faces of magnetic body and magnet elements
- **SOL FORT is more accurate** -- use FORC only for quick estimates
- Face subdivision with `PART <NB>` improves accuracy

## SOL FORT (Maxwell Stress)
- Requires MCM evaluation elements **in air** surrounding the target
- MCM elements must have consistent outward-pointing normals
- Finer mesh in regions of large/varying field
- More accurate than FORC because it evaluates in air (not on material surface)

## SOL FIXB (Lorentz Force on Coils)
- Computes F = IL x B at coil element positions
- NB3 subdivisions in current direction for accuracy
- For MCL2*/MCL1*: specify wire diameter via THIN

## MOMC Limitation
**After SOL MOMC, only FIEL and FIXA are available.**
For sinusoidal force, use the A/P/B oscillation parameters from MOMC results:
```
F(t) = A * cos(2*omega*t + P) + B
```
"""

# ============================================================
# Error messages
# ============================================================

ERROR_MESSAGES = """\
# ELF Error Messages

## Error Types
- **ELF-W(nnn):** Warning -- computation continues
- **ELF-E(nnn):** Error -- computation terminates mid-run
- **ELF-Q(nnn):** Error at end -- computation terminates

## Key Errors by Category

### Matrix Errors (301-323)
| Code | Message | Remedy |
|------|---------|--------|
| 311-319 | MATRIX = 0 / SINGULAR | Check B-H/D-E curve or element shape |
| 322-323 | DGETRS/SGETRS ERROR | PASS LU matrix is abnormal |

### File Errors (401-442)
| Code | Message | Remedy |
|------|---------|--------|
| 402,414-416 | MAT-FILE ERROR OR NO-KEY | Check license key connection |
| 408,413 | MAT-FILE NOT FOUND | Check .mat file in working folder |
| 409-410 | CANNOT WRITE IN DISK | Disk full -- free space or reduce model |
| 441 | NO LICENSE | Wrong HASP key for this software |

### Input Errors (501-599)
| Code | Message | Remedy |
|------|---------|--------|
| 501 | MAI FILE NOT FOUND | Check .mai file |
| 502 | USE LINE NOT FOUND | Fix USE block in .mai |
| 504-505 | MAI-FILE IS NOT MAGIC/ELFIN | Wrong solver for this .mai |
| 508 | SOL MOME/MOMC NOT FOUND | Add mandatory SOL block |
| 509 | MEMORY OVER | Reduce number of elements |
| 581 | UNDEFINED GRID | Check node coordinates in .meg |
| 582-584 | UNDEFINED VECT | Check VEC1 for element |
| 585-586 | UNDEFINED THIN | Add THIN for thin plate element |
| 587 | UNDEFINED AMPE | Add AMP1 for coil |
| 588 | UNDEFINED OHM2 | Add OHM2 for eddy current element |
| 589 | UNDEFINED TURN | Add COI1 for coil |

### Validation Errors (601-695)
| Code | Message | Remedy |
|------|---------|--------|
| 607 | COI1 DIVISION > 100 | Reduce NB1/NB2 to <= 100 |
| 673-674 | ONLY ONE DATA LINE | Add more B-H/D-E data points |
| 677-678 | H/E MUST INCREASE | Fix monotonicity |
| 679 | XT SHOULD BE PLUS | Fix B-H/D-E curve slope |
| 682 | HBCU SHOULD BEGIN (0,0) | Magnetic body curve must start at origin |
| 692-693 | SHAPE OF ELEMENT | Fix element shape |
| 743-744 | DO NOT USE HBA1 AND HBA2 TOGETHER | Remove one |

### Circuit/Limit Errors (701-744)
| Code | Message | Remedy |
|------|---------|--------|
| 701 | CURRENT MID > 1000 | Keep EMFM materials <= 1000 |
| 703 | STAR NEED EMFM | Add EMFM for star-connected coils |
| 716 | FREQ < 1E-10 | Increase frequency |
| 721 | CANNOT USE PASS GENE WITH MOTION | Remove PASS GENE |

### Warnings (901-906)
| Code | Message | Remedy |
|------|---------|--------|
| 901-903 | CHECK DIVISION (NB1,NB2) | Coil cross-section ratio unbalanced |
| 904-905 | XT SHOULD BE PLUS | Smooth B-H/D-E curve |
| 906 | DID NOT CONVERGE | Increase NONL iterations, refine mesh, smooth curve |

### BEAM Messages
| Message | Meaning |
|---------|---------|
| VELOCITY EXCEEDS LIGHT SPEED | Particle too fast -- check VOLB |
| TOO BIG SPEED CHANGE | TIME step too large |
"""

# ============================================================
# MEG Export from Cubit
# ============================================================

MEG_EXPORT = """\
# MEG Export from Cubit / cubit_mesh_export

Cubit-side `cubit_mesh_export` supports ELF-compatible `.meg` export for larger
CAD/mesh workflows. The command-style `radia_export meg` route is also useful
when labels and DIM selection should be specified from a shell or script.

## Python helpers
```python
import cubit_mesh_export

cubit_mesh_export.export_meg(cubit, "model.meg", DIM="T")
cubit_mesh_export.export_3D_meg(cubit, "model")
```

`DIM="T"` is the usual full-3D MAGIC route. Use Cubit headless/batch execution
for automated workflows, then inspect the resulting `.meg` as an ELF input
deck.

## Command
```
radia_export meg "output.meg" [threed|twod|axisymmetric] [labels "1:MMB,2:MWL,..."] [overwrite]
```

## DIM Selection
| Keyword | DIM suffix | Symmetry |
|---------|-----------|----------|
| `threed` | T | Full 3D |
| `twod` | R | 2D cross-section |
| `axisymmetric` | K | Axisymmetric |

## Label Assignment
Each Cubit block gets an ELF element label:
```
labels "1:MMB,2:MWL,3:MCL,4:MCO"
```

## Element Name = PREFIX(3) + NODE_COUNT(1) + DIM(1)
Node count from mesh type (quad=4, tri=3, line=2), DIM from symmetry selection.

## Available Labels by DIM

### T (3D)
MMB, MMS, MMT, MMP, MWL, MWV, MCL, MCO, MAB, MAT, MBB

### K (Axisymmetric) / R (2D)
MMB, MMT, MMP, MWL, MWV, MCL, MCO, MAB, MAT, MBB
"""

# ============================================================
# Examples catalog
# ============================================================

EXAMPLES_CATALOG = """\
# ELF600 Example File Catalog

Located in `C:\\ELF600\\examples\\`.

Use `elf_examples_playbook(limit=100)` for compact cards over 100 example
analyses. Each card summarizes paired `.mai`/`.mei`/`.model` files, detected
SOL blocks, element families, feature tags (for example `flux-linkage`,
`maxwell-force`, `eddy-current`, `sinusoidal-ac`, `motor`), and a reuse hint.
Then call `elf_examples_get(path)` for the raw template.

## beam/ -- Charged Particle Beam Tracking
| Example | Description |
|---------|-------------|
| BASIC/ECB, BECB | Beam in ELFIN field |
| BX01-BX08 | Electron optics (+ m/e variants) |

## elfin/ -- Electrostatic Analysis
| Example | Description |
|---------|-------------|
| BASIC/EMB,EQL,ESC* | Basic electrostatic problems |
| EK/EK01-EK06 | Axisymmetric electrostatic |
| ER/ER01-ER05 | 2D cross-section |
| ET/ET01-ET06 | 3D electrostatic |
| WorkBook/EWork* | Tutorials |

## magic/ -- Magnetostatic Analysis
| Example | Description |
|---------|-------------|
| BASIC/MBCL,HCOIL,... | Simple magnet + coil models |
| MK/MK01-MK06 | Axisymmetric magnetostatic |
| MR/MR01-MR05 | 2D cross-section |
| MT/MT01-MT09 | 3D magnetostatic |
| IPM/Motor1,Motor2 | IPM motor Ld/Lq analysis |
| LscLl/Sample1-6 | Leakage inductance (6 methods) |
| MOMC/MOMCFJ | AC complex force/Joule heat |
| magne/magnetize/ | 5 magnetization cases |
| magne/demagne/ | 4 demagnetization samples |
| WorkBook/Work* | Tutorials |

## No TEAM problem benchmarks are included in the examples.
"""

# ============================================================
# IEmesh Tool
# ============================================================

IEMESH_TOOL = """\
# IEmesh -- Mesh Preprocessor

IEmesh is the integrated mesh creation tool for ELF. It consists of:

## Architecture
- **IEmesh.exe** -- Script editor with Command Guide, Command Filter, Hint View
- **mesh750.exe** -- Script-to-mesh compiler (.mei -> .meg). Requires HASP key.
- **Wmap3.exe** -- 3D visualization of .meg files

## Workflow
1. Create/edit `.mei` script in IEmesh editor
2. mesh750.exe compiles to `.meg`
3. Wmap3 visualizes for verification
4. Iterate

## Script Advantages
- Model creation procedure is saved (reproducible)
- Variable changes update dimensions globally
- Work can be divided among team members

## Command Categories (~18 two-letter families)
| Family | Purpose |
|--------|---------|
| AA | Direct element creation (auto-mesh shapes) |
| AN | Node creation |
| AE | Element creation by nodes |
| AF | Figure (geometry line/circle) creation |
| FN | Figure utilization (intersections, tangents) |
| NB | Names and material IDs |
| SE | Element selection |
| SN | Node selection |
| ME | Element editing (copy, move, extrude, delete) |
| MN | Node editing (copy, move, transform) |
| BE | Element division |
| TE | Element direction |
| GE | Division ratio |
| CL | Clear/delete |
| RB | Renumber |
| VEC | Vector definition |
| PUT | Variable assignment |
| DIM | Array declaration |

## Mathematical Functions
_ABS, _SQRT, _EXP, _LOG, _LOG10, _MAX, _MIN, _INT, _SIGN, _MOD,
_SIN, _COS, _TAN, _ASIN, _ACOS, _ATAN, _ATAN2

## Node/Element Information Functions
_XNODE, _YNODE, _ZNODE, _DIST, _RNODE, _TNODE, _NELEM, _KELEM,
_MNODE, _MELEM, _MMID, _KMID, _MID, _PID, _SEC, _SNC
"""

# ============================================================
# Wmap3 and MagFilter2
# ============================================================

TOOLS_DOCS = """\
# ELF Visualization and Post-Processing Tools

## Wmap3 -- 3D Visualization
- Opens .meg (geometry) and .mag (results) files
- Multiple views with independent rotation/zoom/pan
- Display modes: wireframe, shrink, solid
- Vector plots (field arrows with level colors)
- Contour plots (scalar fields with custom ranges)
- Animation across time steps
- Object selection by node, element, material, coordinates
- Data list for tabular numerical values

## MagFilter2 -- Result Extraction
- Extracts .mag results to CSV for spreadsheet analysis
- Physics tabs: magnetic flux, force, Joule heat, flux linkage, etc.
- Configurable output range, items, units
- Settings saveable for reuse

## MaiEditor3 -- Control File GUI Editor
- Creates/edits .mai files with mode-specific interfaces
- MAGIC mode: B-H curves, permeability, current/voltage, motion, force selection
- ELFIN mode: D-E curves, potential, charge, boundary conditions
- BEAM mode: particle properties, beam info, relativistic effects

## ELF/Bench -- Problem Manager
- Groups linked files as "problems" (.meg, .mai, .mag, .mao, .mas)
- Batch processing of multiple calculations
- Quick-launch of all ELF tools
- Drag-and-drop file registration

## ComplexTransfer2 -- MOMC Animator
- Converts complex .mag to pseudo-transient .mag (N steps per period)
- Enables Wmap3 animation of sinusoidal results
- Usage: `ComplexTransfer.EXE problem.mag 36`
"""

# ============================================================
# Cauer Ladder Network (CLN) extraction from ELF MAGIC output
# ============================================================
#
# Distilled from a rectangular-CLN reference suite (21 Python scripts;
# Cu cuboid 5x2x1 mm benchmark, B_x/B_y/B_z directions, sinusoidal AC
# + transient validation, 2026-04..05).

CLN_EXTRACTION = """\
# ELF MAGIC -> Cauer Ladder Network (CLN) extraction workflow

This topic documents the **post-processing pipeline** for synthesising an
equivalent RL Cauer ladder (or Foster series) of a conductor's eddy-current
response from ELF MAGIC sinusoidal-response output. The reference
implementation is a 21-script rectangular-CLN reference analysis suite.

ELF MAGIC produces field/current data for a list of frequencies via
`SOL MOMC` (sinusoidal MOM Complex). The 4 steps below turn that into a
compact 4-10-stage RL ladder that can be embedded in SPICE / equivalent
circuits and reproduces the ELF response to within 0.1-1% across the
sampled frequency range.

## Step 1 -- ELF MAGIC SOL MOMC run

Choose N frequencies log-spaced over the band of interest (typically
10^2..10^8 Hz for thin metal targets). Example .mai SOL block:

```
SOL MOMC
 FREQ 1   100
 FREQ 2   1000
 FREQ 3   10000
 ...
 FREQ 30  1e8
 BCND, NODES
 RHS  HXYZ  0  0  1     ! drive B_z = mu_0 * H_z = mu_0 unit
END
```

Use the **same conductor mesh** for all frequencies (no remeshing).
Output: `.mag` file with J (real + imag) at each frequency, plus `M1EW`
Joule-loss density per element when requested.

## Step 2 -- Parse `.mag` to extract J at each (x_e, omega)

Key data-line patterns (ASCII format, regex-friendly):

| Line tag | Meaning | Columns (after tag + 4 ints) |
|----------|---------|------------------------------|
| `M3GJG`  | Geometry: node position for nodal-J output | `x y z` (METERS) |
| `M3GJ`   | Real part of nodal J | `Jx_re Jy_re Jz_re` (A/m^2) |
| `M3GJI`  | Imag part of nodal J | `Jx_im Jy_im Jz_im` (A/m^2) |
| `M3EJG`  | Geometry: element centroid (elemental-J output) | `x y z` |
| `M3EJ`   | Real part of element-centroid J | `Jx_re Jy_re Jz_re` |
| `M3EJI`  | Imag part of element-centroid J | `Jx_im Jy_im Jz_im` |
| `M1EW`   | Joule loss density per element (W/m^3) | one column |
| `TOTAL = ` in `.mao` | SOL FORT integrated force | `area flux Fx Fy Fz Tx Ty Tz` |

Parsing convention: line tags repeat for each frequency step; counter-based
parsing collects NEL (or NNODE) consecutive lines per step, then resets.

**Pitfalls**:
- `.mag` is **UTF-8** but `.mao` is **shift_jis** — open with the right codec.
- Coordinates in `.mag` are in **meters** even if the `.mei` input used mm
  (because ELF normalises via GSC=0.001).
- Node-J (`M3GJ*`) gives a (N+1)^3 grid; element-J (`M3EJ*`) gives N^3
  centroids. Choose ONE for moment integration to avoid double-counting.
- Sometimes the geometry block is emitted only at step 0 — use a
  `geom_done` flag and ignore later geom blocks.

## Step 3 -- Compute magnetic-moment admittance Y_ij(i omega)

The driving-direction-j to response-direction-i admittance is

```
Y_ij(i omega) = m_i(i omega) / H_j_applied
m_i = (1/2) integral_V epsilon_ikl x_k J_l dV
```

For the standard cuboid benchmark (B_z driving):

```python
m_z = (1/2) sum_e (x_e * Jy_e - y_e * Jx_e) * V_e
Y_zz = (m_z_real + 1j * m_z_imag) / H_applied
```

Compute Y at all N frequencies; build the data array `(omega_k, Y_k)`.

For full anisotropic susceptibility tensor, run 3 jobs (B_x / B_y / B_z
driving) and stack the 3x3 matrix at each frequency. See `cauer_3dir_full.py`.

## Step 4 -- Foster fit then Cauer synthesis

### Foster (parallel-pole) fit

Model the admittance as a finite Foster series:

```
Y(s) = - mu_0 s sum_{n=1..N_F} a_n / (1 + s tau_n)
```

at s = i omega. Fit by minimising `sum_k |Y_data(omega_k) - Y_foster(omega_k)|^2`
over `(a_n, tau_n)`. Practical pointers:

- Use **scipy.optimize.least_squares** with log(tau_n) and log(a_n) as the
  unknowns to keep the search well-conditioned.
- Initial guesses for tau_n: log-spaced between 1/omega_max and 1/omega_min.
- Increase N_F until the residual stops decreasing; typically 3-5 modes
  capture > 99% of energy for simple cuboid / sphere geometry.
- For higher-N stability, switch to **mpmath** (50 digits) -- the Hankel-
  Pade conditioning blows up around N=6-7 in FP64 (see
  `bem_foster_high_N_stability.py` and `pymor_cauer_RnLn.py`).

### Foster -> Cauer-I (series-pole)

Continued-fraction expansion at s = 0 gives the **Cauer-I R-L ladder**:

```
Y(s) = 1 / (R_0 + 1 / (s L_1 + 1 / (R_2 + 1 / (s L_3 + ...))))
```

Algorithm (see `foster_to_cauer_ELF.py`):
1. Build Y as a rational polynomial num/den in numpy.poly1d from Foster
   `(a_n, tau_n)`.
2. At each stage k: extract constant (or 1/s) part as the next ladder
   element, then invert and subtract; stop when the polynomial degree
   drops below 1.
3. For Cauer-II (series-inductor first) use continued fraction at s -> inf.

### Foster -> Cauer-I (Hankel-Pade route)

The **moment-matching** route is more robust for high-N: extract moments
`m_k = integral of t^k h(t) dt` from Y(s) Taylor series at s=0, then run
QD-Pade / Stieltjes / Wheeler-Lanczos to get the Cauer rungs. See the
parent CLN research line (radia-mcp's `cln_sphere_dd` topic) for a DD
(double-double) version that pushes the precision wall from FP64 stage 4-5
to stage 12+.

## Step 5 -- Cross-validation against ELF transient + force

The synthesised CLN can be checked against three independent ELF outputs:

| Check | Predicted by CLN | ELF source | Pass criterion |
|-------|------------------|------------|----------------|
| Step response m_z(t) | `m_z(t) = -mu_0 H_0 sum (a_n/tau_n) exp(-t/tau_n)` | `.mag` from SOL transient | < 1% relative at all sampled t |
| Joule loss P(omega) | `P(omega) = - (omega/2) Im Y(i omega) * mu_0 * H_0^2 * V` | `.mao` integrated M1EW or `SOL ENGY` | < 1% relative |
| Lorentz force F_z | `F_z = integral_V Re[J x B] / 2 dV` from CLN-reconstructed J,B | `.mao` `SOL FORT` `TOTAL` line | < 1% (Maxwell-stress agreement) |

Scripts: `validate_step_response.py`, `validate_step_fine.py`,
`validate_step_via_fft.py`, `validate_loss.py`, `validate_lorentz.py`,
`check_lorentz_consistency.py`. See also `prony_time_fit.py` for an
independent time-domain Prony fit of m_z(t) that should match the
frequency-domain Foster (a_n, tau_n).

## Step 6 -- Reconciliation and high-precision refinement

For publication-quality cross-platform agreement, combine all 3 datasets
(freq Y, time m(t), force F):

- `joint_freq_time_fit.py` -- joint least squares over both domains.
- `refit_cauer_high_order.py` -- 4..10-stage fits to find the right cutoff.
- `reconcile_and_cauer.py` -- Foster <-> ELF reconciliation followed by
  Cauer-I extraction.

For high-precision (10+ stage) work, use the radia-mcp
`cln_sphere_dd_pipeline` MCP tool's DD pipeline -- it pushes the FP64
precision wall back via double-double arithmetic.

## Quick reference: 21 reference scripts (a rectangular-CLN reference suite)

| Script | Step | Purpose |
|--------|------|---------|
| `parse_mag_compute_Yzz.py` | 2,3 | Element-J -> Y_zz(i omega) for cuboid 5x2x1 |
| `parse_mag_v2_M3GJ.py` | 2,3 | Node-J -> Y via 3D trapezoidal |
| `parse_mag_v3_farfield.py` | 2,3 | Far-field dipole back-extraction (sanity) |
| `parse_lorentz_force.py` | 5 | `.mao` SOL FORT TOTAL parser |
| `bem_foster_high_N_stability.py` | 4 | Vector Fitting stability sweep |
| `cauer_from_elf_30f.py` | 3,4 | 30-freq Foster + Cauer-I |
| `cauer_3dir_full.py` | 4 | Tensor Y_ij + Cauer per direction |
| `cauer_N_step_compare.py` | 5 | N-stage convergence vs ELF transient |
| `elf_cauer_RnLn_highN.py` | 4 | High-N Cauer-I extraction |
| `foster_to_cauer_ELF.py` | 4 | Foster -> Cauer-II continued fraction |
| `joint_freq_time_fit.py` | 4,6 | Joint freq+time fit |
| `prony_time_fit.py` | 4,6 | Time-domain Prony fit |
| `pymor_cauer_RnLn.py` | 4 | pymor Vector Fitting alternative |
| `reconcile_and_cauer.py` | 4,6 | Foster <-> ELF reconciliation |
| `refit_cauer_high_order.py` | 4,6 | N=4..10 stage cutoff finder |
| `validate_step_response.py` | 5 | Step response cross-check |
| `validate_step_fine.py` | 5 | Fine-dt validation |
| `validate_step_via_fft.py` | 5 | FFT-reconstructed step |
| `validate_loss.py` | 5 | Joule loss P(omega) check |
| `validate_lorentz.py` | 5 | Lorentz force F_z check |
| `check_lorentz_consistency.py` | 5 | F_z = integral [Re J x B] / 2 dV cross-check |

## Common Y(s) helper formulas

For the unit-driving cuboid 5x2x1 mm benchmark:

- **Saturation susceptibility** Y_sat = lim_{omega -> inf} Y(i omega) = -V_conductor
  (perfect diamagnetic limit). For 5x2x1 mm: Y_sat = -1e-8 m^3.
- **Low-freq slope** Y(0) = 0 (no DC magnetization for a perfect conductor).
- **Joule loss** P(omega) = -(omega/2) Im{Y(i omega)} * mu_0 * |H_0|^2 * V.
  Cross-check against M1EW total via integral_V M1EW dV.
- **Foster step response** m(t) = -mu_0 H_0 sum (a_n/tau_n) exp(-t/tau_n);
  m(0+) = -V_conductor * H_0 (saturation), m(inf) = 0.

## See also

- `elf_usage("sinusoidal")` for SOL MOMC complex-arithmetic conventions.
- `elf_usage("force_methods")` for FORT / FORC / FIXB Maxwell-stress integration.
- `elf_help_search("M3GJ")` / `elf_help_search("M3EJ")` for raw line specs
  in the MAGIC reference manual.
- The radia-mcp `cln_sphere_dd_pipeline` MCP tool for the DD high-precision
  Cauer pipeline applied to the same workflow on a sphere benchmark.
"""

# ============================================================
# Licensing / dongle (Sentinel HL)
# ============================================================

LICENSING_DOCS = """\
# ELF600 Licensing -- Sentinel HL USB Dongle (HASP)

ELF600 is protected by a **SafeNet/Thales Sentinel HL USB dongle** (formerly
HASP HL). To read the license, the **Sentinel LDK Run-time Environment** must be
installed and the `hasplms` ("Sentinel LDK License Manager") service running.
A healthy dongle enumerates with USB identity **VID_0529 / PID_0001**
("Sentinel HL" / "Sentinel USB Key") and binds the `aksusb` / `akshasp` drivers.

## Admin Control Center (ACC)
The run-time exposes a local web console:

- URL: **http://localhost:1947**  (Sentinel Admin Control Center)
- The "Sentinel Keys" page lists every locally-connected and network key.
- A healthy local dongle appears with `addrs: Local`, a Key ID, and the ELF
  vendor code.

If ELF refuses to start with a licensing error, confirm the key is visible here
first.

## Troubleshooting: dongle not recognized

### Symptom A -- "Unknown USB Device (Device Descriptor Request Failed)"
Device Manager shows the dongle under *Universal Serial Bus controllers* as
**"Unknown USB Device (Device Descriptor Request Failed)"** with a yellow
warning (**Code 43**), and its USB ID is the placeholder **VID_0000 & PID_0002**
(not VID_0529). The ACC shows **no key**.

Meaning: Windows could not read the device descriptor, so it never learns the
dongle is a Sentinel -- an enumeration failure *below* the driver layer. **This
is NOT a missing-driver or bad-install problem** -- re-installing the run-time
does not fix it. It is most commonly seen on **USB 3.x (xHCI) ports**,
front-panel headers, USB hubs, or extension cables.

**Fix -- change the USB port:**
1. Unplug and re-seat the dongle **directly** (no hub / extension / KVM) into a
   different port -- prefer a rear **USB 2.0** port, or go through a powered
   **USB 2.0 hub** (the hub handles enumeration the dongle struggles with on raw
   xHCI). Avoid blue USB 3.x and USB-C ports.
2. On a clean enumeration the device re-appears as **"Sentinel HL" /
   "Sentinel USB Key" (VID_0529 & PID_0001)**, the `aksusb` / `akshasp` drivers
   bind automatically, and `ProblemCode` becomes 0 (status OK).
3. Re-check the ACC (http://localhost:1947) -- the key now appears as
   `addrs: Local`.

Note: `aksusb` binds only **after** a real key enumerates cleanly. If you
inspect during the failure and see "aksusb not installed", that is a *symptom*
of the enumeration failure, not the root cause -- it appears as soon as the key
is read on a good port.

### Symptom B -- key present in ACC but ELF still complains
If the key is visible in the ACC but ELF reports an expired/invalid license,
that is a license-content matter (e.g. a time-limited "Sentinel HL Time" key),
not a connection problem -- the hardware side is fine.

## Windows diagnostics (PowerShell)
```
# Any USB device in an error state (Code 43, etc.)
Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 } |
  Select-Object Name, DeviceID, ConfigManagerErrorCode

# The Sentinel dongle's problem code and bound driver
Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match 'VID_0529' } |
  ForEach-Object { $_ | Get-PnpDeviceProperty `
    -KeyName DEVPKEY_Device_ProblemCode, DEVPKEY_Device_Service }

# License-manager service + drivers
Get-Service hasplms
Get-CimInstance Win32_SystemDriver | Where-Object { $_.Name -match 'aksusb|akshasp' }

# ACC key list (programmatic)
(Invoke-WebRequest 'http://localhost:1947/_int_/devices.html' -UseBasicParsing).Content
```

Clear stale/ghost device records, then force a fresh enumeration:
```
pnputil /remove-device "USB\\VID_0000&PID_0002\\..."   # the failed node(s)
pnputil /scan-devices
```

## See also
- `elf_usage("tools")` for the ELF application tools.
- The Sentinel run-time (HASP driver) is installed together with ELF by the ELF
  setup package; it is not shipped as a standalone installer.
"""


# ============================================================
# Python API
# ============================================================

PYTHON_API_DOCS = """\
# ELF600 Python ctypes API

ELF600 ships two Python ctypes wrappers in the `bin/` directory:

| Wrapper | DLL | Solver |
|---------|-----|--------|
| `magtypes.py` / class `mag` | `magh1600.dll` | MAGIC (magnetostatic / eddy) |
| `elftypes.py` / class `elf` | `elfh1300.dll` | ELFIN (electrostatic) |

Both load the DLL on instantiation and expose all DLL functions as class methods.
The `bin/` directory must be on `PATH`, or the `ELF600_BIN` environment variable
can override the default path in enhanced wrapper versions.

## Calling convention (Fortran pass-by-reference ABI)

**Scalar arguments** are wrapped by the method layer with `ctypes.byref`:
```python
m.SET_AMP1(mid, 100.0)
# internally: dll.SET_AMP1(byref(c_int(mid)), byref(c_double(100.0)))
```

**Array arguments** pass a `numpy.ndarray` directly — dtype must match exactly:
```python
bx = np.zeros(N, dtype=np.float64)   # float64 required
m.GET_FIEL_N(nid, x, y, z, bx, by, bz)   # bx/by/bz populated in-place
```

**String arguments** use `.encode() + b"/"` sentinel (Fortran string terminator);
the wrapper handles this, so callers pass plain Python `str`:
```python
m.START_PRE("MYMODEL")   # internally: dll.START_PRE(b"MYMODEL/")
```

## Method name suffixes

| Suffix | Meaning |
|--------|---------|
| *(none)* | Caller provides pre-allocated numpy output buffers |
| `_V` | Vector variant: coordinates as a shape-`(3,)` float64 array |
| `_A` | Array variant: evaluate at M points simultaneously |
| `_R` | **Return variant** — allocates buffers internally; returns Python values |

Prefer `_R` variants in scripts:
```python
bx, by, bz = m.GET_FIEL_X_R(0.0, 0.0, 0.005)
Bvec = m.GET_FIEL_X_V_R([0.0, 0.0, 0.005])      # shape-(3,) array
fx,fy,fz,tx,ty,tz = m.GET_FORT_R(mid)
flux = m.GET_FLUM_R(mid_target, nb3, mid_source)
```

## End-to-end call sequence (MAGIC)

```python
import os, sys
os.chdir(project_directory)   # START_PRE resolves .mai/.meg from cwd
sys.path.insert(0, elf600_bin_dir)
from magtypes import mag

m = mag()

# 1 — open project (MYMODEL.mai + MYMODEL.meg must exist in cwd)
m.START_PRE("MYMODEL")

# 2 — allocate result storage (n = max element ID in model)
m.SET_NMAD(n);  m.SET_NMAF(n);  m.SET_NMAH(n);  m.SET_NMAO(n)

# 3 — (optional) update excitation before each moment
m.SET_AMP1(1, 100.0)      # 100 A in coil element group 1

# 4 — solve one moment
m.SOL_MOME()

# 5 — retrieve results
bx, by, bz = m.GET_FIEL_X_R(x, y, z)
fx,fy,fz,tx,ty,tz = m.GET_FORT_R(mid)
flux = m.GET_FLUM_R(mid_t, nb3, mid_s)

# 6 — parametric sweep: update excitation, re-solve in a loop
for amp in [50.0, 100.0, 200.0]:
    m.SET_AMP1(1, amp)
    m.SOL_MOME()
    _, _, bz_val = m.GET_FIEL_X_R(0.0, 0.0, 0.01)
    print(f"amp={amp} A  Bz={bz_val*1e3:.3f} mT")

# 7 — per-project cleanup (after all moments for this project)
m.SOL_END()
m.DE_ALLOCATE()
m.CLOSE_FILE()
# m.STOP_DLL()  # omit here; call once at end of the entire Python session
```

Use `RESET_MOME()` to restart the solver from scratch while keeping the project open.

## Key functions reference

### Lifecycle

| Method | Signature | Description |
|--------|-----------|-------------|
| `START_PRE(name)` | `str` | Open project; `name` = file stem (no extension) |
| `SET_NMAG/NMAF/NMAH/NMAO/NMAD(n)` | `int` | Allocate result buffers |
| `SOL_MOME()` | — | Solve one moment / time step |
| `RESET_MOME()` | — | Reset state (keep project open) |
| `SOL_END()` | — | Finalize solution |
| `DE_ALLOCATE()` | — | Free internal arrays |
| `CLOSE_FILE()` | — | Close project files |
| `STOP_DLL()` | — | Unload DLL (once per process) |

### Excitation

| Method | Signature | Description |
|--------|-----------|-------------|
| `SET_AMP1(mid, A)` | `int, float` | Coil current [A] on element group `mid` |
| `SET_VOL1(mid, V)` | `int, float` | Voltage source [V] |
| `SET_OHM1(mid, R)` | `int, float` | Resistance [Ω] |
| `SET_COI1(mid,T,NB1,NB2)` | `int,float,int,int` | Coil: turns, start/end boundary |
| `SET_UNI1(Hx,Hy,Hz)` | `float×3` | Applied uniform H-field [A/m] |
| `SET_VEC3(mid,vx,vy,vz)` | `int,float×3` | Remanence direction (MBB permanent magnet) |
| `SET_VEC1(eid,vx,vy,vz)` | `int,float×3` | Per-element remanence direction |
| `SET_MOV1(mid,x,y,z,t)` | `int,float×4` | Motion: translation + angle [rad] |
| `SET_ORI1(mid,x,y,z,k)` | `int,float×3,int` | Orientation for anisotropic material |
| `SET_TIME(start,step)` | `float×2` | Transient start time and step |
| `SET_NONL(method,n,tol)` | `int,int,float` | Nonlinear iteration control |
| `SET_PASS(n)` | `int` | Number of BEM passes |
| `SET_NCPU(n)` | `int` | CPU thread count |

### B-H curve (nonlinear MAGIC iron)

```python
m.SET_HBID(mid)              # begin curve for element group mid
m.SET_HBUN(mid, "A/m", "T") # unit strings (Fortran string sentinel handled)
m.SET_HBSC(mid, Hs, Bs)     # scale factors (usually 1.0)
for H, B in bh_points:
    m.SET_HBCU(H, B)         # add one point at a time
```

### Field retrieval (_R variants)

| Method | Returns | Description |
|--------|---------|-------------|
| `GET_FIEL_X_R(x,y,z)` | `Bx,By,Bz` | B-field at arbitrary coordinate |
| `GET_FIEL_X_V_R(pos)` | `array(3)` | B-field, vector position input |
| `GET_FIEL_X_A_R(M,X,Y,Z)` | `Bx[M],By[M],Bz[M]` | B-field at M coordinates |
| `GET_FIEL_N_R(nid)` | `x,y,z,Bx,By,Bz` | B-field at mesh node `nid` |
| `GET_FIEL_N_V_R(nid)` | `pos(3),B(3)` | B-field at mesh node (vector) |
| `GET_FORT_R(mid)` | `Fx,Fy,Fz,Tx,Ty,Tz` | Force+torque on element group |
| `GET_FORT_V_R(mid)` | `F(3),T(3)` | Force+torque (vector form) |
| `GET_FIXB_R(mid,n)` | `Fx,Fy,Fz,Tx,Ty,Tz` | Force on fixed boundary |
| `GET_FLUM_R(mid_t,nb3,mid_s)` | `float` | Flux linkage |
| `GET_EMFM_R(mid)` | `amp, emf` | Induced EMF in coil group |
| `GET_NONL_R(i)` | `n, a` | Nonlinear convergence info |

### PUT_MAD: write result data to .mad file

`PUT_MAD_*` writes tagged result records (4-char key, indices i/j, then data):

| Method | Description |
|--------|-------------|
| `PUT_MAD_1(key,i,j,val)` | One scalar |
| `PUT_MAD_3(key,i,j,x,y,z)` | Three scalars |
| `PUT_MAD_6(key,i,j,a,b,c,d,e,f)` | Six scalars (e.g. force+torque) |
| `PUT_MAD_V(key,i,j,arr)` | Shape-`(3,)` array |
| `PUT_MAD_VV(key,i,j,X,Y)` | Two shape-`(3,)` arrays |
| `PUT_MAD_H(key,i,j,arr)` | Shape-`(6,)` array |

### MAGIC eddy current (MAB/MAT element groups)

| Method | Arguments | Description |
|--------|-----------|-------------|
| `SET_EDID(mid)` | `int` | Declare eddy-current group |
| `SET_EDSC(mid,Es,Ds)` | `int,float,float` | σ and scale |
| `SET_EDCU(E,D)` | `float,float` | Global eddy parameters |

### ELFIN field retrieval (electrostatic, elftypes.py)

| Method | Returns | Description |
|--------|---------|-------------|
| `GET_POTE_X_R(x,y,z)` | `float` | Scalar potential φ at coordinate |
| `GET_POTE_N_R(nid)` | `x,y,z, φ` | φ at mesh node |
| `GET_POTE_X_A_R(M,X,Y,Z)` | `array(M)` | φ at M coordinates |
| `GET_POTE_X_V_R(pos)` | `float` | φ, vector position input |

ELFIN material data uses `SET_CHA1/CHA2/VAL1` (charge / permittivity).
ELFIN does not have `GET_FORT`, `GET_FLUM`, or `GET_EMFM`.

## Common pitfalls

- **Working directory**: `START_PRE("NAME")` opens `NAME.mai` + `NAME.meg`
  relative to the current directory. Call `os.chdir(project_dir)` first, or
  pass the full absolute path stem.
- **Buffer dtype**: numpy arrays passed to non-`_R` variants must use exactly
  `dtype=np.float64` or `dtype=np.int32` as declared. Wrong dtype → silent
  data corruption or a ctypes type mismatch.
- **Single session per process**: Only one DLL instance can be active. Creating
  a second `mag()` in the same process is not supported.
- **Cleanup order**: `SOL_END()` → `DE_ALLOCATE()` → `CLOSE_FILE()` per
  project. Call `STOP_DLL()` only once at the very end of a Python process —
  it is a blocking/finalizing call and must **not** be used inside a loop or
  a context manager that wraps individual projects. The context manager
  `__exit__` does **not** call `STOP_DLL()` for this reason.
- **`from magtypes import *`**: This also imports `numpy as np` into the calling
  namespace (magtypes.py imports numpy at module level).

## See also
- `elf_usage("magic")` — MAGIC solver details, .mai keywords, element types
- `elf_usage("elfin")` — ELFIN solver, D-E curves
- `elf_usage("examples")` — Example models (MBCL magnetostatic, ABCL/BBCL transient)
- `elf_usage("bh_curves")` — B-H table format and extrapolation rules
"""


# ============================================================
# Router function
# ============================================================

LIVE_DRIVE_DOCS = """\
# Driving the open MAGIC kernel from Python (live)

The open, dongle-free MAGIC field kernel (this project's open re-implementation,
github.com/ksugahar/ELF) is driven from Python via the `magic_dll.Magic` wrapper
(`src/python` on `sys.path`):

    from magic_dll import Magic
    magic = Magic("build/magic.dll")
    magic.add_element(vertices, material_id=1)      # per tetrahedron (4x3 node coords)
    magic.set_element_magnetization(e, (Mx, My, Mz))
    Bv, Hv = magic.compute_field_at(x, y, z)        # field at a point
    magic.finalize()

Set `KMP_DUPLICATE_LIB_OK=TRUE` when using netgen + magic.dll in the same process.

VERIFIED (2026-06-14): a uniformly magnetized block's on-axis fringe field matches the
exact closed form (Camacho & Sosa, Rev. Mex. Fis. E 59 (2013) 8-17) to ~machine precision
(rel 5.4e-10). Runnable example: `examples/block_magnet_fringe_field/` in the open repo.
This is the live-drive leg used to cross-validate an independent BEM surface-charge solver
against analytic closed forms.
"""


FORCE_GAP_OBSERVABLE_CONTRACT = """\
# PM force-gap observable contract for ELF/MAGIC -> open validation

Use this contract when a MAGIC force observable from `SOL FORC`, `SOL FORT`, or
`SOL FIXB` is being promoted into an open validation row.  This contract tool
does not launch a run or publish product result files; use the guarded local
`elf_product_*` ctypes sequence on a work copy before preparing a public-safe row.

## Minimum row schema

Each row should keep the geometry and force semantics explicit before any
solver comparison:

| Field | Meaning |
|---|---|
| `case_id` | one force-gap sweep identifier |
| `result_set_id` | one solved-result package identifier; do not mix old and new runs |
| `observable_id` | stable force observable/table identifier, e.g. one `FORC` / `FORT` / `FIXB` target |
| `gap_m` | signed-independent mechanical gap in metres; positive scalar |
| `force_N` | force component along the declared approach axis |
| `quantity_dimension` | `2d_per_length` for N/m rows, or `3d_total` for N rows |
| `force_unit` | must match `quantity_dimension`: `N/m` for 2D rows, `N` for 3D rows |
| `component_frame` | global or local frame used by the force component |
| `axis` | force/gap axis, e.g. `z` |
| `sign_convention` | e.g. `attractive_negative` for closing force |
| `force_method` | `FORC`, `FORT`, or `FIXB` |
| `status` | `ok` only after the row parser and unit checks passed |

## Public analytic gate

For coaxial permanent-magnet or dipole-limit teaching checks, the far-field
force magnitude scales as `|F| proportional to 1/g^4`.  Before comparing
detailed BEM values, pass the scrubbed table through the radia-mcp gate
`coaxial_pm_force_gap_sweep_gate(rows)`.

That gate checks:

- every `gap_m` is positive,
- force signs match the declared attraction convention,
- the first/last force ratio agrees with the fourth-power gap ratio, and
- `abs(force_N) * gap_m**4` is approximately invariant across the sweep.

## Negative controls worth keeping

- Flip one force sign; the gate must reject the row set.
- Mix metre and millimetre gaps; the fourth-power invariant should fail
  dramatically.
- Reuse rows from different `case_id` values only after a package identity gate
  has confirmed they describe the same magnet pair and approach axis.
- Change only `result_set_id` or `observable_id`; the parser must reject stale
  force tables before force values are compared.
- Mark a 2D per-length row as `N` or a 3D total-force row as `N/m`; the unit
  and quantity dimension must fail before numerical comparison.

## ELF/MAGIC authoring notes

`SOL MOME` or the appropriate magnetic solve block must run before force
post-processing.  `FORC` and `FORT` are surface/stress-style outputs; `FIXB`
is useful for coil-force checks.  Keep the product-local `.mag` / `.mao`
files and raw numeric result tables outside the public MCP package.  Public
artifacts should retain only the parsed row contract, tolerances, validation
status, and a pointer to the open analytic gate.
"""

MAXWELL_STRESS_SURFACE_PACKAGE_CONTRACT = """\
# Maxwell-stress surface package contract for ELF/MAGIC -> open validation

Use this contract before promoting a `SOL FORT` Maxwell-stress force or torque
result into an open validation row.  This contract tool does not launch the
product or publish product result files; it can still require a clean package
identity so a user-local runner does not mix a stress surface, solve command,
and observable table from different cases.

## Minimum artifact package

Keep these artifacts together before any numerical force/torque value is read:

| Kind | Required fields |
|---|---|
| `stress_surface` | `case_id`, `stress_surface_id`, `result_set_id`, `observable_id`, `closed_surface`, `normal_orientation`, `formulation_id`, `kernel_family`, `singular_treatment`, `symmetry_factor`, `status` |
| `solve_command` | `case_id`, `stress_surface_id`, `result_set_id`, `observable_id`, `sol_command`, `axis`, `formulation_id`, `kernel_family`, `singular_treatment`, `symmetry_factor`, `status` |
| `observable_table` | `case_id`, `stress_surface_id`, `result_set_id`, `observable_id`, `force_method`, `axis`, `sign_convention`, `quantity_dimension`, `force_unit`, `formulation_id`, `kernel_family`, `singular_treatment`, `symmetry_factor`, `status` |

## Public package gate

Pass the scrubbed package through the radia-mcp gate
`maxwell_stress_surface_package_gate(artifacts)` before comparing force or
torque magnitudes.

That gate checks:

- the required artifact kinds are present,
- all rows share the same `case_id`,
- all rows share the same `stress_surface_id`,
- all rows share the same `result_set_id` when present,
- all rows share the same `observable_id` when present,
- the stress surface is explicitly closed,
- `SOL FORT` / `FORT` / Maxwell-stress method semantics are declared,
- the force or torque axis is consistent,
- if `observable_id` names an axis (for example `fort_z_force`), that named
  axis must agree with the package `axis`,
- normal orientation and sign convention are recorded,
- when the package expects a normal orientation such as `outward`, the recorded
  stress-surface normal orientation must match that expected direction,
- when supplied, `formulation_id`, `kernel_family`, and `singular_treatment`
  are consistent across all package artifacts,
- when the package expects a formulation or kernel, the recorded
  `formulation_id` / `kernel_family` must match before values are interpreted,
- when present, `quantity_dimension` and `force_unit` agree (`2d_per_length`
  with `N/m`, `3d_total` with `N`),
- any symmetry factor is positive, and
- artifact statuses are `ok` / `pass` / `verified`.

## Negative controls worth keeping

- Mark the stress surface as open; the package must fail before force values
  are read.
- Change only the observable-table `stress_surface_id`; the package must fail
  as a stale-surface mix.
- Change only the observable-table `result_set_id` or `observable_id`; the
  package must fail as a stale result or wrong observable mix.
- Keep `observable_id=fort_z_force` but change the package axis to `y`; the
  package must fail before the z-force value is read as a y-force.
- Flip the stress-surface `normal_orientation`; the package must fail when
  `expected_normal_orientation` is supplied.
- Change only the observable-table `kernel_family`; the package must fail as a
  stale formulation/kernel mix even when the surface and result ids still match.
- Replace `SOL FORT` with a non-Maxwell-stress force method; the package must
  fail unless a separate method-specific gate is used.
- Attach `quantity_dimension=2d_per_length` to a row whose `force_unit` is
  `N`; the package must fail as a force-unit/quantity mismatch.

## ELF/MAGIC authoring notes

For motor torque or magnet force, prefer `SOL FORT` with a clean closed MCM/ECM
stress surface in air.  `SOL FORC` and other force commands can still be useful,
but they are different observable contracts.  Keep product-local `.mag` /
`.mao` files and raw numeric result tables outside the public MCP package.
Public artifacts should retain only package metadata, tolerances, validation
status, and the open gate name.
"""

_TOPICS = {
    "overview": ELF_OVERVIEW,
    "mai_format": MAI_FORMAT,
    "mei_format": MEI_FORMAT,
    "meg_format": MEG_FORMAT,
    "magic": MAGIC_DOCS,
    "elfin": ELFIN_DOCS,
    "beam": BEAM_DOCS,
    "element_types": ELEMENT_TYPES,
    "bh_curves": BH_CURVES,
    "sol_commands": SOL_COMMANDS,
    "mei_commands": MEI_COMMANDS,
    "ipm_motor": IPM_MOTOR,
    "motor_radia_bridge": MOTOR_RADIA_BRIDGE,
    "inductance": INDUCTANCE_DOCS,
    "magnetization": MAGNETIZATION_DOCS,
    "examples": EXAMPLES_CATALOG,
    "meg_export": MEG_EXPORT,
    "treasure_box": TREASURE_BOX,
    "sinusoidal": SINUSOIDAL_RESPONSE,
    "anisotropy": ANISOTROPY_LAMINATION,
    "sted": STEADY_STATE_EDDY,
    "meshing": MESHING_GUIDELINES,
    "convergence": NONLINEAR_CONVERGENCE,
    "force_methods": FORCE_METHODS,
    "errors": ERROR_MESSAGES,
    "iemesh": IEMESH_TOOL,
    "tools": TOOLS_DOCS,
    "cln_extraction": CLN_EXTRACTION,
    "licensing": LICENSING_DOCS,
    "python_api": PYTHON_API_DOCS,
    "live_drive": LIVE_DRIVE_DOCS,
    "force_gap_contract": FORCE_GAP_OBSERVABLE_CONTRACT,
    "maxwell_stress_surface_package": MAXWELL_STRESS_SURFACE_PACKAGE_CONTRACT,
}


def get_elf_documentation(topic: str = "all") -> str:
    """Return ELF documentation for the given topic."""
    if topic == "all":
        return "\n\n".join(_TOPICS.values())

    result = _TOPICS.get(topic)
    if result is None:
        available = ", ".join(sorted(_TOPICS.keys()))
        return f"Unknown topic: '{topic}'. Available topics: {available}"
    return result
