---
description: "Print almanach pages on the AtomS3R thermal printer. Pair over BLE, print layouts from CLI or the remote rendering service at almanach.crib.scapegoat.dev."
name: almanach-printing
metadata:
  title: Almanach Printing
  topics:
    - almanach
    - printing
    - web-bluetooth
    - ble
    - thermal-printer
  what_for: "Print almanach pages on the AtomS3R thermal printer, pair over BLE, and manage the remote rendering service."
  when_to_use: "Use when the user wants to print something on the almanach printer, pair/re-pair the printer, check printer status, or manage the rendering service."
---

# Almanach Printing Skill

Print almanach pages on the M5Stack AtomS3R thermal printer (ALM_0F2320) using the almanach-render-service. Supports CLI printing, remote printing via `almanach.crib.scapegoat.dev`, and BLE pairing.

## Printer Details

| Detail | Value |
|--------|-------|
| Device name | ALM_0F2320 |
| Current IP | 192.168.0.126 |
| WiFi SSID | yolobolo |
| PoP (proof of possession) | alm-0f2320 |
| Paper width | 384px (58mm, 203dpi K118) |
| Printer baud | 460800 |
| Printer API | `POST http://192.168.0.126/api/print/bitmap` |

## Rendering Service

| Endpoint | URL |
|----------|-----|
| Local health | `http://localhost:8199/health` |
| Remote health | `https://almanach.crib.scapegoat.dev/health` |
| Local render+print | `POST http://localhost:8199/api/render-and-print` |
| Remote render+print | `POST https://almanach.crib.scapegoat.dev/api/render-and-print` |
| Local Studio UI | `http://localhost:8199/almanach` |
| Remote Studio UI | `https://almanach.crib.scapegoat.dev/almanach` |
| Setup page (BLE) | `http://localhost:8199/setup` |

The remote service runs on the crib k3s cluster (Proxmox host at 192.168.0.225), which is on the same LAN as the printer.

## Print Workflow

### 1. Print a YAML layout (CLI)

```bash
cd ~/code/wesen/go-go-golems/almanach
./dist/almanach-render-service print \
  --layout path/to/layout.yaml \
  --printer-ip 192.168.0.126 \
  --feed-lines 8 \
  --output yaml
```

### 2. Print a YAML layout (remote HTTP API)

Convert the YAML to JSON and POST it:

```bash
cat layout.yaml | python3 -c "import sys,yaml,json; print(json.dumps(yaml.safe_load(sys.stdin)))" | \
  curl -sk -X POST https://almanach.crib.scapegoat.dev/api/render-and-print \
  -H "Content-Type: application/json" \
  -d @-
```

### 3. Print a YAML layout (local HTTP API)

```bash
cat layout.yaml | python3 -c "import sys,yaml,json; print(json.dumps(yaml.safe_load(sys.stdin)))" | \
  curl -s -X POST http://localhost:8199/api/render-and-print \
  -H "Content-Type: application/json" \
  -d @-
```

### 4. Render a preview (no print)

```bash
./dist/almanach-render-service render \
  --layout layout.yaml \
  --out /tmp/preview.png \
  --output yaml
```

### 5. Inspect layout metrics

```bash
./dist/almanach-render-service inspect \
  --layout layout.yaml \
  --output yaml
```

## Pairing Workflow

The printer uses ESP-IDF BLE provisioning with Security 1. Pair when the printer is new or after a physical reset.

### Prerequisites

- Printer in BLE provisioning mode (advertising as `ALM_...`)
- BlueZ running (`systemctl status bluetooth`)
- Almanach binary built (`make build`)
- Current WiFi SSID and password

### Pair via native CLI

```bash
# Step 1: Verify BLE connection
./dist/almanach-render-service ble-provision --implementation native \
  --action version --service-name ALM_0F2320 --pop alm-0f2320

# Step 2: Provision WiFi
./dist/almanach-render-service ble-provision --implementation native \
  --action provision --service-name ALM_0F2320 --pop alm-0f2320 \
  --ssid yolobolo --passphrase <PASSWORD>
```

### Pair via Web Bluetooth (browser)

1. Start the setup server: `./dist/almanach-render-service setup --port 8199`
2. Open `http://localhost:8199/setup` in Chrome
3. Enter PoP (`alm-0f2320`), WiFi SSID, password
4. Click "Find BLE printer" → select `ALM_0F2320`
5. Click "Continue provisioning"
6. Printer IP is saved to state file automatically

### Physical reset (fallback)

Long-press the AtomS3R button until the reset threshold. The firmware clears WiFi state and reboots into BLE provisioning mode.

## Layout Format

YAML layouts describe a thermal paper page as blocks. For the **full field reference** with every block type and its data fields, see:

```bash
almanach-render-service help layout-dsl-reference
```

Or read the source directly:
```
~/code/wesen/go-go-golems/almanach/internal/app/doc/layout-dsl-reference.md
```

Quick-start example:

```yaml
almanach_studio_version: 1
theme: minimal
paperWidth: 384
bodyScale: 1.45
feedLines: 3
blocks:
  - id: title-1
    type: title
    data:
      text: MY TITLE
      subtitle: A subtitle
  - id: date-1
    type: date
    data:
      date: May 14, 2026
      day: Thursday
  - id: note-1
    type: note
    data:
      label: Notes
      text: Some text here
      author: Author
  - id: quote-1
    type: quote
    data:
      text: "A quote"
      author: Author
```

Valid block types: `title`, `date`, `divider`, `plan`, `news`, `weather`, `note`, `habits`, `mood`, `reading`, `reflection`, `quote`, `word`, `history`, `did`, `image`.

Each block type has specific data fields — check the DSL reference for the complete list.

### `image` block

Use `image` to embed a photograph or illustration. Images must be provided as URLs or base64 data URLs in the `src` field. For headless/CLI rendering, embed as data URLs so no network fetch is needed.

```yaml
- id: img-1
  type: image
  data:
    label: Banner
    src: data:image/jpeg;base64,/9j/4AAQ...
    alt: A botanical engraving
    caption: Optional caption text
    height: 100
    fit: cover
    border: true
    grayscale: true
```

| Data field | Type | Description |
|---|---|---|
| `label` | string | Section heading above the image. |
| `src` | string | Image URL or `data:image/...;base64,...` data URL. |
| `alt` | string | Alt text. |
| `caption` | string | Caption below the image. |
| `height` | integer | Image height in pixels within the layout. |
| `fit` | string | CSS `object-fit`: `cover`, `contain`, or `fill`. |
| `border` | boolean | Draw a border around the image. |
| `grayscale` | boolean | Render in grayscale (better for thermal printing). |

To embed a local image file as a data URL:

```bash
python3 -c "import base64,sys; print('data:image/png;base64,' + base64.b64encode(open(sys.argv[1],'rb').read()).decode())" /path/to/image.png
```

## Image Library

The skill bundles 138 ready-to-print images in `images/`. These are pre-cropped banner/insert PNGs suitable for the `image` block type at ~500px wide.

| Collection | Count | Description |
|---|---|---|
| `images/animals-grid/` | 30 | Vintage animal engravings: badger, bear, bee, cow, crab, crayfish, dragonfly, fox, frog, goat, goose, hedgehog, hen, horse, loon, moth, owl, pheasant, pig, rabbit, rooster, sheep, snake, songbird, sparrow, squirrel, stag, swan, tortoise, trout |
| `images/cats/` | 28 | Cat/vintage feline engravings — descriptive scene names (e.g. `cat-at-garden-gate.png`, `cat-sleeping-on-windowsill.png`) |
| `images/marine/` | 28 | Marine/nautical engravings — descriptive names (e.g. `lighthouse.png`, `tall-ship.png`, `shipwreck.png`, `seashells.png`) |
| `images/pastoral/` | 30 | Pastoral/countryside engravings — descriptive names (e.g. `stone-wall-gate.png`, `country-windmill.png`, `shepherd-flock.png`) |
| `images/cat-portraits/` | 17 | Cat portrait photographs — breed/color names (e.g. `maine-coon-profile.png`, `tuxedo.png`, `tortoiseshell.png`) + contact sheet |
| `images/animals/` | 5 | Animal illustrations: fish, fox, hedgehog, owl, snake |

Each collection has a `manifest.json` with source metadata. Files are named descriptively so you can pick the right image from the filename alone — e.g. `images/marine/lighthouse.png`, `images/animals-grid/fox.png`, `images/cats/cat-sleeping-on-windowsill.png`.

To use an image in a layout, embed it as a data URL:

```bash
IMG=~/.pi/agent/skills/almanach-printing/images/marine/rowboat.png
DATA_URL=$(python3 -c "import base64,sys; print('data:image/png;base64,' + base64.b64encode(open(sys.argv[1],'rb').read()).decode())" "$IMG")

# Then use $DATA_URL as the `src` value in an image block
```

## Known Issues

- **Large bitmaps are now segmented:** Bitmaps over ~36 KiB are automatically split into segments and sent as sequential print commands. Only the final segment carries the paper feed. This works around the ESP32 httpd's ~38 KiB TCP receive limit.
- **Web Bluetooth requires secure context:** The setup page must run on `localhost` or HTTPS. Remote BLE provisioning is not possible without HTTPS.
- **Google Fonts embedded in SPA:** Docker Chrome renders pixel-identical to local Chrome. The woff2 fonts are bundled as base64 in `fonts.css` — no network fetch needed. Default `ALMANACH_FONT_SCALE=1.4`.

## File Locations

| Item | Path |
|------|------|
| Repo | `~/code/wesen/go-go-golems/almanach` |
| Binary | `~/code/wesen/go-go-golems/almanach/dist/almanach-render-service` |
| State file | `~/.config/almanach/render-service/state.json` |
| crib-k3s manifests | `~/code/wesen/crib-k3s/gitops/kustomize/almanach/` |
| Docker image | `ghcr.io/go-go-golems/almanach-render-service:latest` |
| Example layouts | `~/code/wesen/go-go-golems/almanach/examples/layouts/` |
| Firmware | `~/code/wesen/go-go-golems/almanach/firmware/atoms3r/` |
| Image library | `~/.pi/agent/skills/almanach-printing/images/` |
