# Machine configuration repository

This branch is `machine/amd-laptop` for the AMD HawkPoint laptop (`nlh-cachy`).
The matching Clavis source checkout must use the same branch. Read
[MACHINE-WORKFLOW.md](MACHINE-WORKFLOW.md) before capturing, restoring or porting fixes.
The NVIDIA desktop has its own `machine/nvidia-desktop` branch in both repositories.
Do not merge entire machine branches or overwrite a target with the peer's snapshot.
Port individual reviewed fixes with source attribution, preserving target hardware,
Dock, mouse, display, lyrics and power preferences. Do not apply NVIDIA workarounds
or run the legacy all-in-one Niri build/install flow on this AMD machine.
Use `scripts/capture-machine.py` for snapshots; inspect diffs before committing.
`system-reference/machine` is opt-in reference material, never automatic deployment.
The old Niri/Smithay build recipe is historical; inventory.json records the runtime.
Do not reset local work, install packages or restart services merely to save config.
