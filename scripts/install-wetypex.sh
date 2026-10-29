#!/usr/bin/env bash
set -euo pipefail
version=2.2.3.657-13
if installed=$(pacman -Q fcitx5-wetypex 2>/dev/null); then
    installed=${installed#* }
    if [[ $(vercmp "$installed" "$version") -ge 0 ]]; then
        echo "WeTypeX is already installed: $installed"
        exit 0
    fi
fi
[[ $(uname -m) == x86_64 ]] || { echo 'This pinned WeTypeX package requires x86_64.' >&2; exit 1; }
command -v pkexec >/dev/null || { echo 'Install a graphical polkit authentication agent first.' >&2; exit 1; }
cache_dir=${XDG_CACHE_HOME:-$HOME/.cache}/desktop-config/packages
mkdir -p -- "$cache_dir"
package="$cache_dir/fcitx5-wetypex-$version-x86_64.pkg.tar.zst"
expected=e83faa72aeb0f93d48325640fa723dea65a7a637aca8991c6e0c3be1c0b632f8
if [[ ! -f "$package" ]] || [[ $(sha256sum "$package" | cut -d ' ' -f 1) != "$expected" ]]; then
    temporary=$(mktemp "$cache_dir/.wetypex.XXXXXX")
    trap 'rm -f -- "$temporary"' EXIT
    curl --fail --location --retry 2 --connect-timeout 20 --max-time 300 \
        "https://github.com/panxuc/fcitx5-wetypex/releases/download/v$version/fcitx5-wetypex-$version-x86_64.pkg.tar.zst" -o "$temporary"
    [[ $(sha256sum "$temporary" | cut -d ' ' -f 1) == "$expected" ]] || { echo 'WeTypeX package checksum mismatch.' >&2; exit 1; }
    mv -- "$temporary" "$package"
fi
pkexec /usr/bin/pacman -U --needed "$package"
