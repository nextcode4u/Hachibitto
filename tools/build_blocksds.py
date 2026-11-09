#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build with current BlocksDS while leaving upstream devkitARM Makefiles intact."""
import argparse
import concurrent.futures
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def variable(path, name):
    text = path.read_text().replace('\\\n', ' ')
    match = re.search(r'^\s*(?:export\s+)?' + name + r'\s*[:?]?=\s*(.*)$', text, re.M)
    return match.group(1).split('#', 1)[0].split() if match else []


def run(command):
    subprocess.run([str(x) for x in command], cwd=ROOT, check=True)


def build(args):
    sdk = args.blocksds.resolve()
    os.environ["BLOCKSDS"] = str(sdk)
    tools = args.toolchain
    out = ROOT / 'build/blocksds'
    if args.clean and out.exists():
        shutil.rmtree(out)
    assets = out / 'generated'
    assets.mkdir(parents=True, exist_ok=True)
    libraries = [sdk / 'libs' / x for x in ['libnds', 'maxmod', 'dswifi']]
    elf_files = []
    for cpu in ['arm9', 'arm7']:
        makefile = ROOT / cpu / 'Makefile'
        dirs = [ROOT / cpu / p for p in variable(makefile, 'SOURCES')]
        includes = [ROOT / cpu / p for p in variable(makefile, 'INCLUDES')]
        includes += dirs + [assets] + [p / 'include' for p in libraries]
        sources = sorted({p for folder in dirs if folder.is_dir() for p in folder.iterdir()
                          if p.is_file() and p.suffix in {'.c', '.cpp', '.s'}})
        if cpu == 'arm9':
            for key in ['GRAPHICS', 'BACKGRD', 'SPRITES']:
                for folder in variable(makefile, key):
                    for png in sorted((ROOT / cpu / folder).glob('*.png')):
                        target = assets / png.stem
                        run([sdk / 'tools/grit/grit', png, '-o' + str(target), '-gt', '-mrt', '-mR8', '-mLs', '-gzl', '-mzl'])
                        sources.append(target.with_suffix('.s'))
            for folder in variable(makefile, 'DATA'):
                for binary in sorted((ROOT / cpu / folder).iterdir()):
                    if binary.is_file():
                        run([sdk / 'tools/bin2c/bin2c', binary, assets])
                        sources.append(assets / (binary.name.replace('.', '_') + '.c'))
        prefix = tools / 'arm-none-eabi-'
        gcc, gxx = str(prefix) + 'gcc', str(prefix) + 'g++'
        flags = ['-marm' if cpu == 'arm9' else '-mthumb', '-mcpu=arm946e-s+nofp' if cpu == 'arm9' else '-mcpu=arm7tdmi',
                 '-mtune=arm946e-s' if cpu == 'arm9' else '-mtune=arm7tdmi',
                 '-D' + cpu.upper(), '-D__NDS__=1', '-D__BLOCKSDS__=1', '-ffunction-sections', '-fdata-sections']
        flags += ['-I' + str(p) for p in includes]
        if cpu == 'arm9':
            flags += ['-fomit-frame-pointer', '-ffast-math', '-falign-functions=4', '-frename-registers', '-finline-functions']
        # GCC 16 defaults to C23; upstream C sources use the older C language rules.
        cflags = ['-include', str(ROOT / 'tools/blocksds_compat.h'), '-std=gnu11', '-Dstatic_assert=_Static_assert', '-fcommon', '-O2']
        cppflags = ['-include', str(ROOT / 'tools/blocksds_compat.h'), '-std=gnu++17', '-fno-exceptions', '-fno-rtti', '-O3', '-flto']
        commands, objects = [], []
        for source in dict.fromkeys(sources):
            relative = source.relative_to(ROOT)
            obj = out / cpu / str(relative).replace('/', '_')
            obj = obj.with_suffix(obj.suffix + '.o')
            obj.parent.mkdir(parents=True, exist_ok=True)
            objects.append(obj)
            compiler = gxx if source.suffix == '.cpp' else gcc
            extra = cppflags if source.suffix == '.cpp' else cflags
            # The newer SDK adds ITCM routines; keep Hachibitto's top-level UI/audio
            # unit compact while leaving the CPU/video cores at their upstream -O2.
            if source.name == 'Hachibitto.c':
                extra = [*extra, '-Os']
            if source.suffix == '.s':
                extra = ['-x', 'assembler-with-cpp', '-DSCCMULT=128', '-DAY_UPSHIFT=3', '-DNDS']
            commands.append([compiler, *flags, *extra, '-c', source, '-o', obj])
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(run, commands))
        elf = out / (cpu + '.elf')
        linker = gxx if any(p.suffix == '.cpp' for p in sources) else gcc
        libs = [x for x in variable(makefile, 'LIBS') if x != '-lfat']
        run([linker, *flags[:3], '-flto', '-specs=' + str(sdk / 'sys/crts' / ('ds_' + cpu + '.specs')),
             '-Wl,--gc-sections', '-Wl,-Map,' + str(out / (cpu + '.map')),
             *objects, *['-L' + str(p / 'lib') for p in libraries], '-Wl,--start-group', *libs, *(['-lstdc++'] if linker == gxx else []), '-lm', '-lc', '-Wl,--end-group', '-o', elf])
        elf_files.append(elf)
    name = ''.join(variable(ROOT / 'Makefile', 'TARGET'))
    icon = ROOT / ('C64_icon.bmp' if name == 'GimliDS' else 'logo.bmp')
    run([sdk / 'tools/ndstool/ndstool', '-c', out / (name + '.nds'), '-9', elf_files[0], '-7', elf_files[1],
         '-b', icon, name + ' argv;wavemotion-dave;nextcode4u argv fork'])
    print('Built', out / (name + '.nds'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blocksds', type=Path, default=Path(os.environ.get('BLOCKSDS', '/opt/blocksds/core')))
    parser.add_argument('--toolchain', type=Path, default=Path('/opt/wonderful/toolchain/gcc-arm-none-eabi/bin'))
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--clean', action='store_true')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    build(args)


if __name__ == '__main__':
    main()
