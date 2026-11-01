#!/usr/bin/env bash
# Build the same NetSIO fork Andy uses, with a passive headless result observer.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
source "$root/scripts/env.sh"
rev=7cd1c6459201a123f51fe9924a2c389d9970c052
src="$root/build/atari800-netsio-src"
if [[ ! -d "$src/.git" ]]; then
    mkdir -p "$(dirname "$src")"
    git init "$src"
    git -C "$src" remote add origin https://github.com/mozzwald/atari800.git
    git -C "$src" fetch --depth 1 origin "$rev"
    git -C "$src" checkout --detach FETCH_HEAD
fi
if [[ "$(git -C "$src" rev-parse HEAD)" != "$rev" ]]; then
    echo "Unexpected Atari800 revision in $src; use a fresh build directory" >&2
    exit 1
fi
python3 "$root/integration-tests/atari800/instrument.py" "$src"
cd "$src"
./autogen.sh
./configure --target=default --with-video=no --with-sound=no --enable-netsio \
    CFLAGS='-O2 -D_DEFAULT_SOURCE -D_POSIX_C_SOURCE=200809L'
make -j "${NIO_ATARI800_JOBS:-4}"
printf 'Headless Atari800: %s/src/atari800\n' "$src"
