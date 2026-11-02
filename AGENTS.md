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
Do not reset local work, install packages or restart services merely to save config.
