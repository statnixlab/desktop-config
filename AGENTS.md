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
Niri source is maintained in `/home/nlh/.local/share/niri-source` on
`machine/amd-laptop`, with personal origin `statnixlab/niri-edge`. The `niri` entry
in `sources.lock.json` pins the complete integrated Git commit (`source_mode: git`).
Do not apply an additional Niri or Smithay patch to this source. Keep the source
pin aligned with a saved and published Niri commit, without collecting unrelated
Clavis or desktop work. See `MACHINE-WORKFLOW.md` for the upstream merge workflow.
Do not reset local work, install packages or restart services merely to save config.
