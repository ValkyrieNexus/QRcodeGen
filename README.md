# QR Code Creator for Autodesk Fusion

A free, open-source addon for Autodesk Fusion (formerly Fusion 360) that generates QR codes as extruded 3D bodies — designed for multi-color 3D printing.

## Features

- **Creation Modes**: Simple text, Website URL, vCard (contact info), WiFi credentials, Sequence (batch numbered QR codes)
- **Placement Modes**:
  - **Standalone** — generates a freestanding QR code component with base plate, frame, and modules
  - **Place on Face** — select a face on an existing body, and the QR code is generated directly on it with automatic scaling and centering. Cuts a recess and fills with colored bodies for multi-color printing
- **Styles**: Square or Circle (dot) modules
- **Configurable**: Segment size, segment spacing, frame border, extrude depth/height, error correction level (L/M/Q/H)
- **Center Logo**: Built-in icons, custom SVG import, or "Empty Center" (clears center zone so you can place your own logo manually)
- **Combined Bodies**: All QR modules are combined into a single `QR_Modules` body instead of hundreds of individual bodies — clean body tree, easy to move and assign colors
- **Multi-Color Ready**: Separate bodies for base plate, frame, modules, and icon — assign different filament colors in your slicer (Bambu Studio, PrusaSlicer, etc.)
- **No External Dependencies**: Pure-Python QR code library bundled — no pip install needed

## Installation

### Step 1: Download

Download the latest release as a ZIP file, or clone this repository:

```
git clone https://github.com/ValkyrieNexus/QRcodeGen.git
```

### Step 2: Copy to Fusion AddIns Directory

Copy the entire `QRcodeGen` folder to your Fusion AddIns directory:

| OS | Path |
|----|------|
| **Windows** | `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\` |
| **Mac** | `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/` |

> **Tip**: You can find this path in Fusion by going to **Utilities > Add-Ins**, clicking the green **+** button, and noting the directory it opens.

> **Important**: Do NOT place the addon on a cloud-synced drive (OneDrive, Dropbox, etc.) as this can cause issues.

### Step 3: Enable in Fusion

1. Open Autodesk Fusion
2. Go to **Utilities > Add-Ins** (or press **Shift+S**)
3. In the **Add-Ins** tab, find **QRcodeGen**
4. Click **Run**
5. Optionally check **Run on Startup** to auto-load

A **QR Code Creator** button will appear in the **DESIGN > CREATE** panel in the toolbar.

## Usage

### Standalone Mode (Freestanding QR Code)

1. Click **QR Code Creator** in the CREATE panel
2. Select a **Creation Mode** (Simple, Website, vCard, WiFi, or Sequence)
3. Enter your data (URL, text, contact info, etc.)
4. Configure style options:
   - **Style**: Square or Circle modules
   - **Segment Size**: Size of each QR module (default 2mm)
   - **Frame**: Optional border frame
   - **Depth / Height**: Extrusion depth (default 0.60mm)
   - **Icon**: Optional center logo (built-in, custom SVG, or Empty Center)
   - **Error Correction**: L (7%), M (15%), Q (25%), H (30%)
5. Click **OK**
6. The QR code is generated as a component with separate bodies:
   - `QR_BasePlate` — the background (assign light/white filament)
   - `QR_Frame` — border frame (assign dark filament)
   - `QR_Modules` — all QR modules combined into one body (assign dark filament)
   - `QR_Icon` — center logo if selected (assign any filament)

### Place on Face Mode (QR on Existing Body)

This mode generates the QR code directly on a face of an existing body — no manual positioning needed.

1. Click **QR Code Creator**
2. In the **Placement** section, change Mode to **Place on Face**
3. Click **Select** next to Target Face and click a **planar face** on your design
4. The addon will:
   - Auto-scale the QR code to fit within the face (with 5% padding)
   - Center the QR on the face
   - Cut module-shaped recesses into the body (if "Cut recess into body" is checked)
   - Fill the recesses with new bodies for multi-color printing
5. Toggle **Cut recess into body**:
   - **Checked** (default): Cuts pockets into the body, then fills them with QR bodies flush with the surface
   - **Unchecked**: Only extrudes QR bodies outward from the face (use when you've already created a recess)

### Adding a Center Logo

For best results with logos, use the **Empty Center** option:

1. Set **Icon** to **Empty Center** — this clears the center zone of the QR code
2. Generate the QR code
3. Manually import your SVG logo using Fusion's **Insert > Insert SVG** tool
4. Position and scale the logo in the center zone
5. Extrude the logo as a new body

This gives you full control over logo orientation and positioning.

### Multi-Color 3D Printing with Bambu Studio

Fusion's 3MF export does not support multi-color filament assignment for Bambu Studio. Use the built-in **Export QR for Bambu** command instead:

#### Step 1: Generate the QR Code

1. Use **Place on Face** mode to generate the QR code on your design
2. Configure Cut Depth and Fill Height as needed

#### Step 2: Export for Bambu

1. Click **Export QR for Bambu** in the CREATE panel (next to QR Code Creator)
2. Select an output folder
3. The addon exports two STL files:
   - `placard.stl` — your design body (the background/base)
   - `qr_modules.stl` — all QR module bodies (the dark squares)

#### Step 3: Import into Bambu Studio

1. Open Bambu Studio
2. **File > Import** (or Ctrl+I)
3. Navigate to the folder where you saved the STLs
4. **Select BOTH files at once** (hold Ctrl and click both `placard.stl` and `qr_modules.stl`)
5. Click Open
6. Bambu Studio will ask: **"Do you want to load these files as one single object with multiple parts?"** → Click **Yes**
7. If asked about scaling to millimeters → Click **Yes**

#### Step 4: Assign Colors

1. In the left sidebar, expand the object to see both parts
2. Right-click the placard part → assign your background filament (e.g., white)
3. Right-click the QR modules part → assign your QR color filament (e.g., black)
4. Slice and print!

> **Note:** The two STL files share the same coordinate origin from Fusion, so they will align perfectly when imported together.

### Multi-Color with Other Slicers

For PrusaSlicer or other slicers that support multi-part objects, the same two-STL workflow applies. Import both files and use your slicer's multi-material/multi-part features to assign different filaments.

## Creation Modes

| Mode | Description | Example |
|------|-------------|---------|
| **Simple** | Free-form text | Any text string |
| **Website** | URL with https:// prefix | `https://example.com` |
| **vCard** | Contact card with name, phone, email, address | Business card QR |
| **WiFi** | WiFi credentials (SSID, password, encryption) | Guest network access |
| **Sequence** | Batch numbered QR codes using `/#/` placeholder | `Part /#/` → Part 001, Part 002, ... |

## Requirements

- Autodesk Fusion (any edition, including Personal/Free)
- Windows or macOS
- No additional Python packages required (QR library is bundled)

## File Structure

```
QRcodeGen/
  QRcodeGen.py              # Entry point
  QRcodeGen.manifest         # Addon metadata
  config.py                  # Constants and defaults
  commands/
    generateQR/
      entry.py               # Command UI + execute handler
      qr_logic.py            # QR matrix generation, vCard, WiFi encoding
      fusion_geometry.py      # Sketch drawing, extrusion, face placement
      icons.py               # Built-in icon definitions
      resources/              # Toolbar icons
  lib/
    qrcode/                  # Vendored pure-Python QR library (MIT license)
```

## License

This project is open source. The bundled `qrcode` library is licensed under the MIT License.
