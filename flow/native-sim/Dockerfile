# Reproduction recipe for the manually built comparison runtime.
# Recipe itself has not yet been rebuilt end-to-end; see README.md.
FROM --platform=linux/amd64 tapeoutbench-eda:latest AS legacy
FROM --platform=linux/arm64 python@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential autoconf automake libtool bison flex gperf git curl ca-certificates llvm-19-dev clang-19 lld-19 libpolly-19-dev libreadline-dev libncurses-dev libsuitesparse-dev libedit-dev zlib1g-dev libzstd-dev pkg-config file
COPY --from=legacy /foss/pdks/ihp-sg13g2/COMMIT /foss/pdks/ihp-sg13g2/COMMIT
COPY --from=legacy /foss/pdks/ihp-sg13g2/libs.tech/ngspice /foss/pdks/ihp-sg13g2/libs.tech/ngspice
COPY --from=legacy /foss/pdks/ihp-sg13g2/libs.tech/verilog-a /foss/pdks/ihp-sg13g2/libs.tech/verilog-a
COPY --from=legacy /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice
COPY --from=legacy /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice
RUN test "$(cat /foss/pdks/ihp-sg13g2/COMMIT)" = 84374023ee8b4b126bebbba67fcbada0a9c0ff0b
WORKDIR /build
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o rustup-init.sh && sh rustup-init.sh -y --profile minimal --default-toolchain 1.98.1
RUN git clone https://github.com/OpenVAF/OpenVAF-Reloaded.git && git -C OpenVAF-Reloaded checkout fdf2522b70f42793f64b1c72f0195c96dea0cc19
RUN git clone --depth 1 --branch ngspice-46 https://github.com/imr/ngspice.git ngspice && test "$(git -C ngspice rev-parse HEAD)" = ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6
RUN git clone --depth 1 --branch ngspice-47 https://github.com/imr/ngspice.git ngspice47 && test "$(git -C ngspice47 rev-parse HEAD)" = a80f6e3e95d51534905b1f23410a951802666656
RUN git clone https://github.com/steveicarus/iverilog.git && git -C iverilog checkout eda9fdcd13d7566b9aab29a8a098e2f4189ea3f3
ENV PATH=/usr/lib/llvm-19/bin:/root/.cargo/bin:/usr/local/bin:/usr/bin:/bin
ENV LLVM_SYS_191_PREFIX=/usr/lib/llvm-19 CARGO_BUILD_JOBS=2 RAYON_NUM_THREADS=2
RUN cd OpenVAF-Reloaded && cargo build --locked --release -p openvaf-driver --features llvm19
RUN tar -C /foss/pdks -cf /build/pdk-models.tar ihp-sg13g2
COPY build-runtime.sh /build/build-runtime.sh
RUN sh /build/build-runtime.sh
RUN mkdir -p /opt/openvaf/bin && cp /build/OpenVAF-Reloaded/target/release/openvaf-r /opt/openvaf/bin/
ENV PATH=/opt/ngspice-46/bin:/opt/iverilog/bin:/usr/local/bin:/usr/bin:/bin
ENV LD_LIBRARY_PATH=/opt/iverilog/lib PDK_ROOT=/foss/pdks PDK=ihp-sg13g2
WORKDIR /work
