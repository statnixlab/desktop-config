#!/usr/bin/env python3
"""Prepare the tested WPS/Zotero add-ons with a fresh local pairing token."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'system-reference/wps-zotero'


def fetch(source, target):
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == source['sha256']:
        return
    subprocess.run(['curl', '--fail', '--location', '--retry', '2', '--connect-timeout', '20',
                    '--max-time', '300', source['url'], '-o', str(target)], check=True)
    if hashlib.sha256(target.read_bytes()).hexdigest() != source['sha256']:
        raise ValueError('Add-on download checksum mismatch')


def prepare(output, cache):
    if output.exists():
        raise ValueError('Output already exists; choose a new directory to preserve the previous token pair')
    cache.mkdir(parents=True, exist_ok=True)
    sources = json.loads((REFERENCE / 'easy-cite/sources.json').read_text())
    wps_tar = cache / 'wps-zotero.tar.gz'
    citation_xpi = cache / 'zotero-citation.xpi'
    fetch(sources['wps'], wps_tar)
    fetch(sources['easier_citation'], citation_xpi)
    token = secrets.token_hex(32)
    with tempfile.TemporaryDirectory(prefix='wps-zotero-') as temporary:
        staging = Path(temporary)
        with tarfile.open(wps_tar) as archive:
            archive.extractall(staging / 'wps', filter='data')
        original = next((staging / 'wps').iterdir())
        for relative in ['proxy.py', 'main.js', 'index.html', 'lang.cfg',
                         'js/ribbon.js', 'js/wpsif.js', 'js/i18n.js', 'LOCAL-INSTALL.txt']:
            source = REFERENCE / relative
            if source.is_file():
                shutil.copy2(source, original / relative)
        bridge = (REFERENCE / 'easy-cite/src/wps-bridge.js').read_text()
        assert bridge.count('__BRIDGE_TOKEN__') == 1
        (original / 'js/easy-cite-bridge.js').write_text(bridge.replace('__BRIDGE_TOKEN__', token))
        addon = staging / 'citation'
        addon.mkdir()
        with zipfile.ZipFile(citation_xpi) as archive:
            for name in archive.namelist():
                path = Path(name)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('Invalid XPI path')
            archive.extractall(addon)
        subprocess.run(['git', 'apply', str(REFERENCE / 'easy-cite/easier-citation.patch')],
                       cwd=addon, check=True)
        script = addon / 'chrome/content/scripts/index.js'
        data = script.read_text()
        assert data.count('__BRIDGE_TOKEN__') == 1
        script.write_text(data.replace('__BRIDGE_TOKEN__', token))
        manifest = json.loads((addon / 'manifest.json').read_text())
        manifest['version'] = '0.5.11.1'
        manifest['applications']['zotero'].pop('update_url', None)
        (addon / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        output.mkdir(parents=True, mode=0o700)
        shutil.copytree(original, output / 'wps-zotero_0.2.0')
        result = output / 'easier-citation-wps-linux-0.5.11.1.xpi'
        with zipfile.ZipFile(result, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(addon.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(addon))
        result.chmod(0o600)
        (output / 'wps-zotero_0.2.0/js/easy-cite-bridge.js').chmod(0o600)
    print('Prepared a new paired add-on set:', output)
    print('Follow system-reference/wps-zotero/README.md to install it. Do not publish the generated pair.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path, default=Path.home() / '.cache/desktop-config/wps-zotero')
    args = parser.parse_args()
    prepare(args.output_dir.expanduser().absolute(), args.cache_dir.expanduser().absolute())


if __name__ == '__main__':
    main()
