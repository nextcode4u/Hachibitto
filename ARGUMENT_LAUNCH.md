# Starting MSX media from a launcher

This fork adds optional `argv[1]` selection to
[Hachibitto](https://github.com/wavemotion-dave/Hachibitto) by wavemotion-dave and its
credited contributors. Existing media loading, mapper selection and machine
initialization remain upstream's implementation.

```text
argv[0] = sd:/apps/Hachibitto.nds
argv[1] = sd:/roms/MSX/My Game.rom
```

Supported file arguments, matched without case sensitivity:

| Extension | Initial media slot |
| --- | --- |
| `.rom`, `.bin`, `.mx2` | Cartridge 1 |
| `.dsk`, `.mxd` | Disk |

The MSX2 aliases `.mx2` and `.mxd` route to the same loaders as `.rom` and `.dsk`;
these aliases do not add new media formats. Only one startup file is selected.
The complete path, including spaces, must be one argument. Valid media skips the
startup selection menu/instructions and goes through the existing
`LoadGameIntoMedia`, configuration/CRC and mapper checks before CPU initialization.
The instruction setting is changed in memory for this startup only; the adapter
does not write a global configuration file.

Both `sd:/` and `fat:/` select their mounted card before relative resource/config
lookups. Relative paths are resolved before the normal browser changes directory.
The chosen media's directory becomes the working directory, matching browser loads.
The adapter fits upstream's fixed buffers: directory paths must be under 200 bytes
and basenames under 132 bytes. Missing, empty, unsupported or overlong input falls
back to the regular media menu, as does an initial media read failure. No argument
keeps normal startup behavior.

Keep upstream's required resources, machine firmware and configuration in their
usual places; argv does not bypass those requirements or change firmware terms.

## Source changes

`arm9/source/argv_launch.c` and its two small headers implement the adapter. The
only existing application source changed is `Hachibitto.c`, with hooks after FAT
initialization and before the normal selection menu. The original Makefiles are
unchanged. This branch started from upstream commit
`08edf9423a0c005cc58bf448901626ea2d637bf6`.

## Building

### Optional current BlocksDS build

The original devkitARM/libnds Makefiles remain available with their original SDK
requirements. To build using current BlocksDS instead, run the separate adapter:

```sh
python3 tools/build_blocksds.py --clean
```

Requirements are Python 3.9 or later, BlocksDS 1.25 (including libnds, Maxmod,
DSWiFi and its asset tools), and the Wonderful ARM GCC toolchain. Local builds used
Wonderful GCC 16.2. Defaults are `/opt/blocksds/core` and
`/opt/wonderful/toolchain/gcc-arm-none-eabi/bin`; override them using `--blocksds`
and `--toolchain`. `BLOCKSDS` also supplies the SDK default. Use `--jobs` to control
parallel compilation.

The adapter reads upstream's source/include/asset/library lists and writes all
objects, generated graphics, linker maps and the NDS file under `build/blocksds/`.
It rebuilds all selected sources each run. A forced compatibility header isolates
legacy formatted-output and heap-helper names from the new SDK. The application's
normal Makefiles and SDK headers are not patched. This is a build option, not an
upstream SDK migration or proof of hardware timing/audio compatibility.

A complete BlocksDS build and the sanitized host tests passed locally. DSi-mode melonDS checks through Gloam verified argv cartridge startup through
the MSX2 firmware and into a game intro using a `.mx2` file. Disk boot, general
title compatibility, performance, saves and physical-console behavior remain
unverified.

The adapter compiles the top-level `Hachibitto.c` UI/audio unit with `-Os` so the
new SDK's routines fit physical 32 KiB ITCM; CPU/video emulation units retain
upstream's `-O2`. The tested map uses 32,736 bytes of ITCM (32 bytes spare), so
future changes must be checked against the linker map. The linker memory limits
have not been enlarged. Performance impact has not been measured on hardware.

## Keeping up with upstream

The `argv-launch` branch contains the fork additions; `main` is kept as an upstream
baseline. Startup adapters and host tests are separate files, and the original
loading routines remain responsible for file decoding and emulation. The small
hooks in existing source are the expected merge points.

```sh
git remote add upstream https://github.com/wavemotion-dave/Hachibitto.git  # Once, if not already configured.
git fetch upstream
git switch argv-launch
git merge upstream/main
sh tests/run-argv-tests.sh
```

Rebuild after merging. If upstream adds native argument support, retire the adapter
rather than layering a second startup loader over it.

## Validation and licensing

Run `sh tests/run-argv-tests.sh` with a C/C++ compiler supporting AddressSanitizer and
UndefinedBehaviorSanitizer. These tests exercise the actual adapter against small
host API doubles and synthetic files: path bounds, spaces, extension matching,
missing files and one-shot selection. They do not run a DS CPU or prove that a
game/book works on a console.

The source and assets inherited from upstream retain their original authors,
credits and terms. New integration files are MIT-licensed as described in
[ARGUMENT_LAUNCH_LICENSE.md](ARGUMENT_LAUNCH_LICENSE.md); this does not relicense the
application or its dependencies. No game, book or separately supplied BIOS is
added by this fork. The download-only argv development release includes a standalone binary, notices and matching source; see [release builds](RELEASE_BUILD.md).
