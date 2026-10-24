#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir=${NIRI_SOURCE_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/niri-desktop-source}
prefix_dir="$HOME/.local/lib/niri-desktop"
[[ $# -eq 0 || ( $# -eq 1 && $1 == --prepare-only ) ]] || {
    echo 'Usage: build-niri.sh [--prepare-only]' >&2; exit 2;
}
python3 "$repo_dir/scripts/prepare-niri.py" "$source_dir"
[[ ${1:-} != --prepare-only ]] || exit 0
command -v cargo >/dev/null || { echo 'Install Rust through install-arch-dependencies.sh first.' >&2; exit 1; }
cargo build --manifest-path "$source_dir/Cargo.toml" --locked --release --package niri \
    --target-dir "$source_dir/target" --jobs "${CARGO_BUILD_JOBS:-4}"
mkdir -p -- "$prefix_dir" "$HOME/.local/bin"
temporary=$(mktemp "$prefix_dir/.niri.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT
install -m 755 "$source_dir/target/release/niri" "$temporary"
mv -f -- "$temporary" "$prefix_dir/niri"
echo "Pinned Niri is ready: $prefix_dir/niri"
echo 'The running compositor was not restarted. The new version takes effect at the next Niri login.'
