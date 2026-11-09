#!/usr/bin/env bash
set -euo pipefail
# Release 17 fixes swallowed digits in GTK4 Chinese input (verified in Nautilus).
version=2.2.3.657-17
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
expected=69489a90d29fea48bf3cdd0aa19e43e73b570df2caeb842ac4199efe2c7e63da
if [[ ! -f "$package" ]] || [[ $(sha256sum "$package" | cut -d ' ' -f 1) != "$expected" ]]; then
    temporary=$(mktemp "$cache_dir/.wetypex.XXXXXX")
    trap 'rm -f -- "$temporary"' EXIT
    curl --fail --location --retry 2 --connect-timeout 20 --max-time 300 \
        "https://github.com/panxuc/fcitx5-wetypex/releases/download/v$version/fcitx5-wetypex-$version-x86_64.pkg.tar.zst" -o "$temporary"
    [[ $(sha256sum "$temporary" | cut -d ' ' -f 1) == "$expected" ]] || { echo 'WeTypeX package checksum mismatch.' >&2; exit 1; }
    mv -- "$temporary" "$package"
fi
pkexec /usr/bin/pacman -U --needed "$package"
