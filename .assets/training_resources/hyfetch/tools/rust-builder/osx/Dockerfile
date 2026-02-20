FROM crazymax/osxcross:11.3-alpine AS osxcross

FROM alpine

# Install Rust building environment
RUN apk add --no-cache curl gcc musl-dev openssl-dev bash clang lld
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Add toolchains for building for macOS[x86_64, aarch64]
RUN /root/.cargo/bin/rustup toolchain install beta && \
    /root/.cargo/bin/rustup default beta
RUN /root/.cargo/bin/rustup target add x86_64-apple-darwin aarch64-apple-darwin

# Copy osxcross toolchain
# RUN apt-get update && apt-get install -y clang lld libc6-dev
ENV PATH="/osxcross/bin:$PATH"
ENV LD_LIBRARY_PATH="/osxcross/lib:$LD_LIBRARY_PATH"
COPY --from=osxcross /osxcross /osxcross
