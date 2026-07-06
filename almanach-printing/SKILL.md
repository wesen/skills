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

### 1. Preferred: print through the crib remote service

Use the `print-remote` verb. It loads YAML/JSON or ZIP layout bundles locally, converts them to the JSON expected by the service, and POSTs to `https://almanach.crib.scapegoat.dev/api/render-and-print`. This avoids hand-written YAML-to-JSON HTTP pipelines and uses the remote service on the same LAN as the printer.

```bash
cd ~/code/wesen/go-go-golems/almanach
./dist/almanach-render-service print-remote \
  --layout path/to/layout.yaml \
  --output yaml
```

Dry-run against the remote render endpoint without printing:

```bash
./dist/almanach-render-service print-remote \
  --layout path/to/layout.yaml \
  --dry-run \
  --output yaml
```

Use ZIP bundles when local image assets should be inlined automatically:

```bash
./dist/almanach-render-service print-remote \
  --layout layout-bundle.zip \
  --output yaml
```

### 2. Local direct printer path (fallback)

Use this only when the remote service is unavailable or when explicitly testing the direct ESP32 printer endpoint. Direct local printing renders with local Chrome and POSTs the bitmap to the printer IP.

```bash
cd ~/code/wesen/go-go-golems/almanach
./dist/almanach-render-service print \
  --layout path/to/layout.yaml \
  --printer-ip 192.168.0.126 \
  --feed-lines 8 \
  --web-dir ~/code/wesen/go-go-golems/almanach/web/dist \
  --output yaml
```

### 3. Render a preview (no print)

```bash
./dist/almanach-render-service render \
  --layout layout.yaml \
  --out /tmp/preview.png \
  --web-dir ~/code/wesen/go-go-golems/almanach/web/dist \
  --output yaml
```

### 4. Inspect layout metrics

```bash
./dist/almanach-render-service inspect \
  --layout layout.yaml \
  --output yaml
```

### 5. Render from a template with data context

Layout files can contain `{{variable}}` expressions that are resolved from a separate data context file or inline flags:

```bash
# From a template + data file
./dist/almanach-render-service print-remote \
  --layout path/to/template.yaml \
  --data path/to/data.yaml \
  --output yaml

# With inline variable override
./dist/almanach-render-service render \
  --layout template.yaml \
  --data data.yaml \
  --define "title=OVERRIDE TITLE" \
  --out /tmp/preview.png

# Inline only (no data file). Multiple values are comma-separated in one flag.
./dist/almanach-render-service render \
  --layout template.yaml \
  --define "title=HELLO,date=May 26, 2026" \
  --out /tmp/preview.png
```

Template expressions: `{{key}}` (required), `{{key:fallback}}` (with default), `{{$ENV_VAR}}` (from environment), `{{$ENV_VAR:fallback}}` (environment with fallback). Use `--define`, not `-D`; no short `-D` alias exists. Inline defines override values loaded from `--data`.

When no `--data` or `--define` is provided, template resolution is skipped entirely, so literal `{{...}}` strings remain unchanged. Almanach no longer fetches or invents content: YAML/layout files and explicit data contexts are the only content sources. If no layout is supplied, the app renders only the minimal scaffold (title + date).

See `examples/templates/` for ready-to-use template + data context pairs.

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

YAML layouts describe a thermal paper page as blocks. For knowledge-strip or technical-summary prints, prefer a readable almanach rhythm instead of dense text-only output:

- Use `bodyScale: 1.42` by default for readable technical almanachs. Use `bodyScale: 1.3` only when the page is too long or the user asks for a more compact print. Avoid going much larger unless the page is very short.
- Include one `image` block for visual rhythm unless the user explicitly asks for text-only. The bundled image library works well; `animals-grid/owl.png`, `animals-grid/fox.png`, and `marine/lighthouse.png` are good generic technical-summary choices.
- Keep `word` block `word` values short — roughly 16 characters maximum. Use `context`, `call ctx`, `owner`, or `runtime`, not package-qualified identifiers like `runtimebridge.CurrentContext(vm)`.
- Put long API names, function signatures, URLs, and code identifiers in `note` blocks rather than `word` blocks.
- For final print copies, prefer `feedLines: 8` so there is enough tear-off paper.

For the **full field reference** with every block type and its data fields, see:

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
bodyScale: 1.42
feedLines: 8
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
  - id: word-1
    type: word
    data:
      word: context
      definition: Short word fields fit the thermal width better.
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
    height: 160
    fit: cover
    border: true
    grayscale: true
    thermalTone: normal
```

| Data field | Type | Default | Description |
|---|---|---|---|
| `label` | string | `"Image Plate"` | Section heading above the image. |
| `src` | string | `""` | Image URL or `data:image/...;base64,...` data URL. Required. |
| `alt` | string | `""` | Alt text. Falls back to `caption`. |
| `caption` | string | `""` | Caption below the image. |
| `height` | integer | `160` | Image height in pixels, clamped 48–420. |
| `fit` | string | `"cover"` | CSS `object-fit`: `cover` (fill, crop) or `contain` (fit, letterbox). |
| `border` | boolean | `true` | Draw a border around the image. |
| `grayscale` | boolean | `true` | Render in grayscale (better for thermal printing). |
| `thermalTone` | string | `"normal"` | Tone preset: `normal` (high contrast) or `light` (brighter, for faint source images). |

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
| Docker image | `ghcr.io/go-go-golems/almanach:sha-<commit>` (GitOps-managed immutable tag) |
| Example layouts | `~/code/wesen/go-go-golems/almanach/examples/layouts/` |
| Firmware | `~/code/wesen/go-go-golems/almanach/firmware/atoms3r/` |
| Image library | `~/.pi/agent/skills/almanach-printing/images/` |
