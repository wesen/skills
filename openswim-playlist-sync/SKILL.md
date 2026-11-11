---
name: openswim-playlist-sync
description: Load talks from the "Swim" YouTube playlist (or any video IDs) onto a Shokz OpenSwim bone-conduction MP3 player — detect and mount the device, download with yt-dlp, split into 15-minute segments, clear the drive, copy in explicit playback order via mtime, sync, unmount, and report what is on the device. Use when the user mentions the OpenSwim, Shokz player, "the swim playlist", asks what is on the OpenSwim, or asks to load/swap/clear talks on it.
---

# OpenSwim Playlist Sync

End-to-end control of the Shokz OpenSwim MP3 player: what's on it, clearing it,
and loading lectures from the canonical **Swim** playlist in a chosen order.

All actions go through `scripts/swimctl` next to this file.

```bash
S=~/.pi/agent/skills/openswim-playlist-sync/scripts/swimctl
```

## Commands

```bash
$S status                 # device, mount state, free space, tracks in play order
$S playlist               # list the Swim playlist (index, title, video id)
$S mount | $S unmount
$S clear                  # remove all *.mp3 from the device

# Load in argument order (order = the order you pass the ids)
$S load jXa8dHzgV8U M-jTeBCEGHc IRJDwtAreB4
$S load --dry-run ID...            # plan only, no device writes
$S load --no-clear ID...           # append instead of replacing
$S load --segment 600 ID...        # override split length (seconds)
$S load --keep-work ID...          # force re-download and re-split
$S load --quiet ID...              # stage summaries only, no per-file lines
```

`load` does: download → split → plan names → clear → copy → set mtimes →
`sync` → verify order → unmount. It is safe to re-run; downloads and segments
are reused from the work dir.

`load` narrates each stage so a failed run is diagnosable from its output alone:

- `[1/N] <id> <title>` + duration and the expected segment count
- download progress throttled to one line per 10%, then size and elapsed time;
  `audio cached:` / `segments cached:` when reusing the work dir
- plan totals: segment count, total bytes, and the first segment of each talk
- preflight: mount point, free space vs. required bytes (aborts if short),
  and how many existing tracks will be removed
- per-file copy lines `[07/15] name 17.8 MB  128891979 / 261264387 bytes`
- hard abort if the device disappears mid-copy
  (`device disappeared after 8/15 files — unplugged?`), plus a final
  copy count vs. on-disk count check before `sync` and unmount

Work dir defaults to `~/.cache/openswim` (`$OPENSWIM_WORK` overrides it).
Set `$OPENSWIM_NO_UNMOUNT=1` to leave the device mounted for inspection.

## Key facts (verified on hardware)

- **Playback order is filesystem mtime order** — oldest first. Not alphabetical,
  not FAT directory order. `swimctl` sets `base + 60*n` seconds so the numbered
  files play in sequence.
- **Never set mtimes with `touch -m -t "<composed string>"`.** A malformed
  value is silently mis-parsed and *inverts* the whole order. Use epoch math:
  `touch -m -d "@$((base + 60*(i-1)))" file`.
- **The device is not always `sda`.** Find the `ONSEMI LC8234xx17S_EVK` row in
  `udisksctl status` and use that device's `1` partition. `swimctl` always
  detects; it never assumes `/dev/sda1`.
- **The player must be powered on** to expose storage. If the ONSEMI entry
  shows 0 B with no partition, it is plugged in but off — power it on/replug.
- **No screen, no rewind, no seek.** Split long talks so you never need to skip
  back; 15 min (`900s`) is the verified default. The trailing segment of a talk
  is naturally shorter.
- **Download to the work dir, never straight to the vfat device** — direct
  transfers stall or leave partial files.
- **Run `sync` before unmounting**, otherwise files can be missing on the
  device after a quick replug.
- Splitting uses `-f segment -segment_time N -c copy` — lossless and fast.
- Stale `yt-dlp` is the usual cause of HTTP 403: `yt-dlp -U` before debugging
  cookies or player clients.

## The Swim playlist

Canonical source for what goes on the player:

```
https://www.youtube.com/playlist?list=PLaKN83gQzNgQ
```

Owned by Manuel Odendahl, grows frequently (44 entries as of 2026-11-01).
Do **not** hardcode the episode list in docs — run `$S playlist` when the
current contents matter, and pass the ids you want to `load`.

Older yt-dlp builds returned `NA` for the bare playlist URL; if that happens,
use a watch URL carrying the same list:

```bash
yt-dlp --flat-playlist --print "%(playlist_index)s. %(title)s [%(id)s]" \
  "https://www.youtube.com/watch?v=<any_id_in_playlist>&list=PLaKN83gQzNgQ"
```

## Reporting to the user

After any `load`/`clear`, state what is on the device: total segments, size
used, and the talks in playback order with their segment ranges and source
video ids. `$S status` prints exactly that in playback order.

Removing a subset of talks means re-running `load` with only the ids to keep
(the mtime base is "now", so appending with `--no-clear` would put new tracks
*at the front* of playback order).

## Files

- `scripts/swimctl` — the whole workflow (status/playlist/load/clear/mount).
- Repo docs worth refreshing if behavior changes:
  `playbooks/03-copy-audio-to-openswim.md` and
  `docs/runbook-openswim-transfer.md` in `~/code/wesen/claw-stuff`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `OpenSwim not found` | Unplugged or powered off | Plug in, power on, re-run |
| ONSEMI listed but 0 B, no partition | Player off / bad state | Power on, replug |
| `sda1` is a different USB stick | Device letters vary | Let `swimctl` detect; never hardcode |
| Files missing after unplug | No `sync` | `$S unmount` (syncs first) |
| Order wrong on playback | Wrong/duplicate mtimes | Re-run `load`; check `$S status` |
| yt-dlp 403 | Stale binary | `yt-dlp -U` |
| `Permission denied` writing | Dirty FAT | Unmount, `fsck.vfat /dev/sdX1`, remount |
