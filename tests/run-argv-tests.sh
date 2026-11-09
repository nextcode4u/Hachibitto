#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
cd "$(dirname "$0")/.."
output=$(mktemp -d)
trap 'rm -rf "$output"' EXIT HUP INT TERM
cc -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror -fsanitize=address,undefined -Iarm9/source tests/argv_path_test.c -o "$output/argv-path-test"
"$output/argv-path-test"
cp arm9/source/argv_launch.c "$output/argv_launch.c"
cc -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror -fsanitize=address,undefined -Itests/stubs -Iarm9/source "$output/argv_launch.c" tests/argv_launch_test.c -o "$output/argv-launch-test"
"$output/argv-launch-test"
