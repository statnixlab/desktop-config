# Niri compatibility patch

`niri-desktop.patch` preserves the local HiDPI Genie coordinate correction,
its geometry tests, and PipeWire SHM mapping/frame pacing adjustments. It also
adds two optional output workarounds. Apply it only to the commit in
`sources.lock.json`; the installer verifies the patch SHA-256 first.

The patched source is [StatIndet/niri-edge](https://github.com/StatIndet/niri-edge),
derived from [niri-wm/niri](https://github.com/niri-wm/niri). Its GPL-3.0-or-later
license applies to the source and these changes. No machine-specific executable
is stored in this repository.

## Scope: one affected computer, not a desktop-wide default

**The flicker was observed on this RTX 4070 SUPER / P2710V computer at 4K160.
The owner reports that another computer running the same operating system and
desktop environment works normally. Its hardware is not assumed to be identical.**
This is a workaround for the affected machine, not evidence that every CachyOS,
Clavis, Niri or NVIDIA installation needs these settings.

Both new debug options default to `false`. They are not enabled in `config/`,
`hardware/`, the standard restore, or the `--same-hardware` restore.
The optional entrypoint and service example live in
[`system-reference/nvidia-flicker/`](../system-reference/nvidia-flicker/), which
is excluded from automatic restoration.

## Optional output settings

- `prefer-16bit-output` tries ABGR16161616F (AB4H) first, with the existing
  AB30 / AR24 / AB24 fallbacks. `disable-10bit-output` takes precedence.
  Pair with the existing `restrict-primary-scanout-to-matching-format` when
  testing, so ordinary fullscreen client buffers cannot bypass the selected
  format. This does not request HDR or a particular display-signal bit depth.
- `force-full-repaint` resets swapchain buffer ages before each scheduled DRM
  render. Composed frames repaint the full output while preserving opaque-region
  occlusion. It does not create a continuous redraw timer or disable direct
  scanout by itself.

On 2026-10-18, the user confirmed that the **combined FP16 + full-repaint +
matching-format scanout restriction** removed the flicker on this machine.
The running build and AB4H output at 3840×2160, 160 Hz, scale 2 were verified.
FP16 alone did not fix Niri; full repaint without FP16 was not compared.
Plasma's PreferAccuracy mode also removed the observed flicker in the comparison.

FP16 uses 8 bytes per pixel, twice the storage of the previous 32-bit buffer
format. Full repaint can increase GPU work, memory bandwidth and buffer
allocation; scanout restriction can add composition work in fullscreen use.
The net performance and power cost has not been measured under a controlled
workload. See the machine-specific reference for setup, rollback and validation
limits.
