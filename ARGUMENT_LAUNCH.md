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
added by this fork. No binary release has been published for this change.
