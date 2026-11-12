# Machine configuration repository

This branch is `machine/nvidia-desktop` for the NVIDIA desktop (`cachyos`).
The matching Clavis source checkout must use the same branch. Read
[MACHINE-WORKFLOW.md](MACHINE-WORKFLOW.md) before capturing, restoring or porting fixes.
The AMD laptop has its own `machine/amd-laptop` branch in both repositories.
Do not merge entire machine branches or overwrite a target with the peer's snapshot.
Port individual reviewed fixes with source attribution, preserving target hardware,
Dock, mouse, display, lyrics and power preferences. AMD-only changes must not remove
this desktop's required GPU, suspend or application compatibility workarounds.
Use `scripts/capture-machine.py` for snapshots; inspect diffs before committing.
`system-reference/machine` is opt-in reference material, never automatic deployment.
The old Niri/Smithay build recipe is historical; inventory.json records the runtime.
Niri source is maintained in `/home/nlh/.local/share/niri-source`, with personal
origin `statnixlab/niri-edge`, on `machine/nvidia-desktop`. It is official niri
plus a personal patch stack; updates rebase it onto `official/main` (see
MACHINE-WORKFLOW.md). StatIndet/niri-edge is no longer followed. Smithay is maintained
at `/home/nlh/.local/share/smithay-source` in `statnixlab/smithay` on the same
machine branch. Keep its required retained-frame patch; do not use the AMD
laptop's unpatched dependency. sources.lock.json and Cargo.lock pin integrated
Git commits. Do not reapply additional Niri or Smithay patches. Publish changed
Smithay source first, then Niri, then the configuration lock. Preserve unrelated
Clavis work and avoid full capture when only updating source references.
Do not reset local work, install packages or restart services merely to save config.
