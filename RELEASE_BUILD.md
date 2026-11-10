# Building an argv release

The fork keeps upstream's devkitARM Makefiles and emulation code. Its optional
BlocksDS adapter uses BlocksDS 1.25.0 and Wonderful GCC 16.2.0:

```sh
sh tests/run-argv-tests.sh
python3 tools/build_blocksds.py --clean --jobs 4
# Commit source changes before preparing an identified release.
python3 tools/build_release.py --tag v1.9-argv.1 --skip-build
```

`tools/release-dependencies.json` identifies checksum-pinned SDK, libnds, Maxmod
and DSWifi sources selected by BlocksDS 1.25.0. The release script checks a clean
source tree and SDK version, caches those sources in `build/release-cache/`, and
includes them in the source package under `dependencies/`. Copy those archives
back into the cache for offline packaging. Building uses the installed matching
SDK/libraries and Wonderful compiler.

The ignored `dist/` output contains a standalone `Hachibitto.nds`, runtime ZIP,
matching source, build identity and checksums. Notices accompany both the runtime
and source downloads. Existing upstream authors, component notices and
noncommercial conditions remain applicable; new argv adapters and build tools
have their separate MIT grant. Thanks to Dave Bernazzani (wavemotion-dave),
Marat Fayzullin (fMSX), Fredrik Ahlstrom (FluBBa sound cores) and Aleksey Vaneev
(LZAV).

The source and binary inherit upstream embedded MSX firmware and graphics whose
redistribution permissions remain unconfirmed. This fork does not establish a
new grant for those materials or add external BIOS files, games or user data.
Install the executable with a compatible homebrew launcher and configure its
file associations as needed. Preserve the accompanying notices and matching
source; this release does not expand upstream redistribution permissions.

`tools/notices/gcc-COPYING.RUNTIME` retains the GCC Runtime Library Exception 3.1.
`tools/notices/picolibc-COPYING` retains the Wonderful Picolibc notice collection
from revision `770d868896622d726129fa99168d5d20160d0f55`:
https://codeberg.org/WonderfulToolchain/wf-picolibc/src/commit/770d868896622d726129fa99168d5d20160d0f55/COPYING.picolibc.
Other SDK/runtime notices come from the exact pinned archives. The source keeps
all original component headers; runtime notices also retain their leading notices.

This is a development build. Cartridge argv startup has been exercised in a
DSi-mode emulator; disk boot, saves, performance and physical-console behavior
remain unverified. Keep checking the physical 32 KiB ITCM limit after changes;
the build adapter does not enlarge linker memory limits.
