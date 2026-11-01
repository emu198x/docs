FROM rust:1.99.1-slim-bookworm AS toolchain
FROM ubuntu:24.04
COPY --from=toolchain /usr/local/rustup /usr/local/rustup
COPY --from=toolchain /usr/local/cargo /usr/local/cargo
ENV PATH=/usr/local/cargo/bin:$PATH RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/target/cargo-home CARGO_TARGET_DIR=/target/build CARGO_BUILD_JOBS=1 CARGO_INCREMENTAL=0 CARGO_PROFILE_DEV_DEBUG=0 CARGO_PROFILE_TEST_DEBUG=0
RUN apt-get update && apt-get install -y --no-install-recommends build-essential pkg-config libudev-dev libasound2-dev ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["cargo", "test", "--locked", "-p", "runtime-commodore-amiga", "--test", "a1200_board_baseline", "--", "--nocapture"]
