#!/usr/bin/env bash

set -e

# Add cargo to path
export PATH="$HOME/.cargo/bin:$PATH"
cd /app

# Set linkers for cross-compilation
export CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER=musl-gcc
export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_LINKER=/musl/aarch64/bin/musl-gcc
export CARGO_TARGET_ARMV7_UNKNOWN_LINUX_MUSLEABIHF_LINKER=/musl/armv7l/bin/musl-gcc
export CARGO_TARGET_RISCV64GC_UNKNOWN_LINUX_MUSL_LINKER=/musl/riscv64/bin/musl-gcc

# Build for windows
cargo build --release --target x86_64-pc-windows-gnu

# Add -C relocation-model=static to the build command
# See https://github.com/rust-lang/rust/issues/95926
export RUSTFLAGS="-C relocation-model=static"

# Build for platforms
cargo build --release --target x86_64-unknown-linux-musl
cargo build --release --target aarch64-unknown-linux-musl
cargo build --release --target armv7-unknown-linux-musleabihf
#cargo build --release --target riscv64gc-unknown-linux-musl
