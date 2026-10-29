#!/usr/bin/env python3
"""Install a prepared WPS add-on without copying Zotero profiles or libraries."""
import argparse
from datetime import datetime
import importlib.util
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def install(prepared, home):
    source = prepared / 'wps-zotero_0.2.0'
    if not (source / 'js/easy-cite-bridge.js').is_file() or '__BRIDGE_TOKEN__' in (source / 'js/easy-cite-bridge.js').read_text():
        raise ValueError('Run prepare-wps-zotero.py first to generate the paired add-ons')
    if home.resolve() == Path.home().resolve():
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():
                continue
            try:
                name = (proc / 'comm').read_text().strip()
            except OSError:
                continue
            if name in ['wps', 'et', 'wpp', 'wpspdf', 'zotero']:
                raise RuntimeError('Quit WPS and Zotero before replacing the add-on')
    destination = home / '.local/share/Kingsoft/wps/jsaddons/wps-zotero_0.2.0'
    if not destination.parent.resolve().is_relative_to(home.resolve()):
        raise ValueError('Add-on destination escapes target home')
    backup = home / '.local/state/desktop-config-backups' / datetime.now().strftime('wps-zotero-%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True)
    if destination.exists():
        shutil.move(destination, backup / 'wps-zotero_0.2.0')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    for name in ['publish.xml', 'jsplugins.xml']:
        target = destination.parent / name
        if target.exists():
            tree = ET.parse(target)
            shutil.copy2(target, backup / name)
        else:
            tree = ET.ElementTree(ET.Element('jsplugins'))
        root = tree.getroot()
        for child in list(root):
            if child.tag == 'jsplugin' and child.get('name') == 'wps-zotero':
                root.remove(child)
        attributes = dict(name='wps-zotero', type='wps', url='http://127.0.0.1:21931/', version='0.2.0')
        if name == 'publish.xml':
            attributes.update(enable='enable_dev', install='null')
        ET.SubElement(root, 'jsplugin', attributes)
        tree.write(target, encoding='utf-8', xml_declaration=True)
    spec = importlib.util.spec_from_file_location('app_install', ROOT / 'scripts/install-app-compat.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    relative = '.config/systemd/user/wps-zotero-proxy.service'
    source_unit = ROOT / 'system-reference/user-home/config/systemd/user/wps-zotero-proxy.service'
    helper.write_file(home, relative, source_unit.read_text().replace('@HOME@', str(home)).encode(), 0o644, backup)
    if home.resolve() == Path.home().resolve():
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', '--now', 'wps-zotero-proxy.service'], check=True)
    print('WPS add-on installed. Backup:', backup)
    print('In Zotero, install this paired XPI from Tools > Add-ons:',
          prepared / 'easier-citation-wps-linux-0.5.11.1.xpi')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prepared_dir', type=Path)
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    prepared = args.prepared_dir.expanduser().absolute()
    home = args.target_home.expanduser().absolute()
    if not args.apply:
        print('Plan: install WPS add-on and proxy from', prepared, 'to', home, '; add --apply to proceed.')
        return
    install(prepared, home)


if __name__ == '__main__':
    main()
