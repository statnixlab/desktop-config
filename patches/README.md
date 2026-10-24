# Niri compatibility patch

`niri-desktop.patch` preserves the local HiDPI Genie coordinate correction,
its geometry tests, and PipeWire SHM mapping/frame pacing adjustments. It also
adds optional output workarounds, per-surface blur strength, and titlebar column sizing. Apply it only to the commit in
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

Output workaround flags default to `false`; the refresh threshold is unset by default. They are not enabled in `config/`,
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

## Additions captured on 2026-10-23

- `background-effect.blur-passes` controls application blur independently of the
  global panel blur, with the `per_surface_blur` IPC capability.
- `layout.client-maximize-to-column` makes client maximize requests use the
  column-width behavior; the titlebar integration tests are included.
- `debug.high-refresh-workaround-above` limits explicitly enabled output
  workarounds to modes strictly above the configured refresh rate.
- `debug.full-repaint-reuse-buffers` offers full-output damage without resetting
  swapchain buffer ages. It remains opt-in, as do the other output workarounds.

The complete current source delta, including the new titlebar test file, is
preserved against the unchanged pinned base commit. Local entrypoint examples
are saved under `system-reference/user-home/`; they are not automatically enabled.

## Verified retained-frame workaround (2026-10-24)

`smithay-retain-frame.patch` is the exact diff from [Smithay PR #2151](https://github.com/Smithay/smithay/pull/2151),
head `0c649d2d6824b60b7bfe27f1fdb5f2fbf4311ac4`, applied to the pinned Smithay
`22571baa20d34d71092942dbb520c4e3fbbd6263`. The upstream MIT license applies;
see `Smithay-LICENSE.txt`. The PR is not merged as of this snapshot.

The Niri integration adds `debug.keep-previous-frame-buffer` (default off),
sets it on output creation and policy changes, and respects the existing
refresh-rate threshold. At 4K160 the verified output is AB30, retained buffer
on, full repaint off, FP16 off, matching-format restriction off. The user
confirmed no flicker and later confirmed success after restoring Orca GPU acceleration.

The mechanism retains the retiring primary swapchain buffer for one extra
frame. It uses an additional buffer and can increase damage redraw; no
controlled performance/power measurements were performed. This replaces the
older workaround only in the optional machine configuration.

The builder prepares both pinned sources and compares the complete patched
working tree before reuse. Local edits or unexpected untracked files stop the
build. The original user's installed compositor is never restarted by it.
