#!/usr/bin/env bash
# This script does some file path magic to make cargo publish work without having
# to have neofetch & font logos in the cargo root.
# ...okay basically it copies these files over before publishing.
set -euo pipefail

# Get the directory of SRC root which is ../ from this script
SRC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CARGO_ROOT="$SRC_ROOT/crates/hyfetch"

# Copy neofetch from here to cargo root
cp "$SRC_ROOT/neofetch" "$CARGO_ROOT/"
mkdir -p "$CARGO_ROOT/hyfetch"
cp -r "$SRC_ROOT/hyfetch/data" "$CARGO_ROOT/hyfetch/"

# Build the crate
cargo publish -p hyfetch --allow-dirty "$@"

# Delete the copied files
rm "$CARGO_ROOT/neofetch"
rm -rf "$CARGO_ROOT/hyfetch"

echo "Done!"