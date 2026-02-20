FROM debian

# Install Rust building environment
RUN apt update && apt install -y curl build-essential gcc libssl-dev bash musl-tools mingw-w64 \
    gcc-arm-linux-gnueabihf gcc-aarch64-linux-gnu gcc-riscv64-linux-gnu
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Add toolchains for building for musl[x86_64, aarch64, armv7l, riscv64], windows[x86_64]
RUN /root/.cargo/bin/rustup target add \
    x86_64-unknown-linux-musl aarch64-unknown-linux-musl armv7-unknown-linux-musleabihf riscv64gc-unknown-linux-musl \
    x86_64-pc-windows-gnu

# Compile musl for multiple architectures
RUN curl "https://musl.libc.org/releases/musl-1.2.5.tar.gz" --output musl.tgz && \
    tar -xvf musl.tgz && \
    cd musl-*/ && \
    ./configure --prefix=/musl/aarch64 --exec-prefix=/musl/aarch64 --target=aarch64-linux-gnu --enable-wrapper=all && \
    make -j18 install && \
    make clean && \
    ./configure --prefix=/musl/armv7l --exec-prefix=/musl/armv7l --target=arm-linux-gnueabihf --enable-wrapper=all && \
    make -j18 install && \
    make clean && \
    ./configure --prefix=/musl/riscv64 --exec-prefix=/musl/riscv64 --target=riscv64-linux-gnu --enable-wrapper=all && \
    make -j18 install && \
    make clean && \
    cd .. && \
    rm -rf musl-*
