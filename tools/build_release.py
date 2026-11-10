#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package the argv build with pinned SDK sources and redistribution notices."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def dependency(item, cache):
    path = cache / item['archive']
    if not path.exists():
        request = urllib.request.Request(item['url'], headers={'User-Agent': 'Hachibitto-release'})
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read(64 * 1024 * 1024 + 1)
        if len(content) > 64 * 1024 * 1024 or sha256(content) != item['sha256']:
            raise ValueError('Dependency download mismatch: ' + item['archive'])
        path.write_bytes(content)
    content = path.read_bytes()
    if sha256(content) != item['sha256']:
        raise ValueError('Dependency cache mismatch: ' + item['archive'])
    return content


def source_archive(path, files):
    with path.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as packed:
        with tarfile.open(fileobj=packed, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name, content in sorted(files.items()):
                info = tarfile.TarInfo('Hachibitto/' + name)
                info.size, info.mode, info.mtime = len(content), 0o644, 0
                archive.addfile(info, io.BytesIO(content))


def build(tag, skip_build=False):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', tag):
        raise ValueError('Use a simple version tag')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise ValueError('Commit source changes before preparing a versioned release')
    sdk = Path(os.environ.get('BLOCKSDS', '/opt/blocksds/core'))
    if (sdk / 'version.txt').read_text().strip().removeprefix('v') != '1.25.0':
        raise ValueError('Review dependency pins before packaging another SDK')
    if not skip_build:
        subprocess.run(['python3', 'tools/build_blocksds.py', '--clean'], cwd=ROOT, check=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    compiler = Path('/opt/wonderful/toolchain/gcc-arm-none-eabi/bin/arm-none-eabi-gcc')
    gcc = subprocess.check_output([str(compiler), '-dumpfullversion'], text=True).strip()
    lock = json.loads((ROOT / 'tools/release-dependencies.json').read_text())
    cache = ROOT / 'build/release-cache'
    cache.mkdir(parents=True, exist_ok=True)
    sources, notices = {}, {}
    for key, item in lock.items():
        content = dependency(item, cache)
        sources['dependencies/' + item['archive']] = content
        with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as archive:
            names = list(item['notices'])
            if key == 'blocksds-sdk':
                names += [m.name.removeprefix(item['directory'] + '/') for m in archive.getmembers()
                          if m.isfile() and m.name.startswith(item['directory'] + '/sys/crts/COPYING.')]
            for name in names:
                value = archive.extractfile(item['directory'] + '/' + name).read()
                if not value.strip():
                    raise ValueError('Empty dependency notice: ' + name)
                notices[key + '-' + Path(name).name] = value
    for name in ['README.md', 'ARGUMENT_LAUNCH.md', 'ARGUMENT_LAUNCH_LICENSE.md']:
        notices[name] = (ROOT / name).read_bytes()
    for path in (ROOT / 'tools/notices').iterdir():
        if path.is_file():
            notices[path.name] = path.read_bytes()
    notices['ATTRIBUTION.md'] = (
        '# Hachibitto argv fork\n\nHachibitto: Dave Bernazzani (wavemotion-dave), based on fMSX by Marat Fayzullin.\n'
        'Original application terms prohibit commercial use; new argv adapters, tests and build tools retain MIT terms.\n'
        'AY38910 and SCC sound cores: Fredrik Ahlstrom (FluBBa). LZAV: Aleksey Vaneev.\n'
        'Includes BlocksDS/libnds, Maxmod and DSWifi with their separate runtime notices.\n'
        'The upstream embedded MSX firmware and graphics remain inherited; redistribution permissions are unconfirmed.\n'
        'This fork adds no external BIOS or games and does not grant rights over inherited firmware or assets.\n'
        'Matching source accompanies this release. Runtime notice provenance is recorded in RELEASE_BUILD.md.\n').encode()
    # Preserve complete initial component notices, without copying implementation into the runtime ZIP.
    components = ['arm9/source/lzav.h', 'arm9/source/teenysha1.h',
                  'arm9/source/cpu/z80/cz80/Z80.h', 'arm9/source/V9938.h',
                  'arm9/source/cpu/ay38910/AY38910.s', 'arm9/source/cpu/scc/SCC.s']
    for name in components:
        lines = (ROOT / name).read_text().splitlines()
        notice = []
        in_block = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('/*'):
                in_block = True
            if not stripped or in_block or stripped.startswith(('//', ';@')):
                notice.append(line)
                if '*/' in stripped:
                    in_block = False
                continue
            break
        if not notice:
            raise ValueError('Component notice missing: ' + name)
        notices['components/' + Path(name).name + '.txt'] = ('\n'.join(notice) + '\n').encode()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in filter(None, tracked):
        # Upstream screenshots, prebuilt executables and blank disk are not build inputs.
        if name.startswith(('images/', 'techdocs/')) or Path(name).suffix.lower() in {'.nds', '.elf', '.d64'}:
            continue
        sources[name] = (ROOT / name).read_bytes()
    sources.update({'release-notices/' + name: data for name, data in notices.items()})
    binary = (ROOT / 'build/blocksds/Hachibitto.nds').read_bytes()
    info = {'tag': tag, 'commit': commit, 'blocksds': '1.25.0', 'gcc': gcc,
            'target': 'tools/build_blocksds.py', 'binary_sha256': sha256(binary), 'dependencies': lock}
    encoded = (json.dumps(info, indent=2) + '\n').encode()
    sources['BUILD-INFO.json'] = encoded
    out = ROOT / 'dist' / tag
    out.mkdir(parents=True, exist_ok=True)
    source_archive(out / f'Hachibitto-{tag}-source.tar.gz', sources)
    with zipfile.ZipFile(out / f'Hachibitto-{tag}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        runtime = {'Hachibitto.nds': binary, **{'licenses/' + name: data for name, data in notices.items()}}
        for name, data in sorted(runtime.items()):
            metadata = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            metadata.compress_type = zipfile.ZIP_DEFLATED
            metadata.external_attr = 0o100644 << 16
            archive.writestr(metadata, data)
    (out / 'Hachibitto.nds').write_bytes(binary)
    (out / 'BUILD-INFO.json').write_bytes(encoded)
    paths = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
    (out / 'SHA256SUMS').write_text(''.join(sha256(p.read_bytes()) + '  ' + p.name + '\n' for p in paths))
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--skip-build', action='store_true')
    arguments = parser.parse_args()
    build(arguments.tag, arguments.skip_build)
