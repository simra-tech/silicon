#!/bin/sh
set -eu
export PATH=/usr/lib/llvm-19/bin:/root/.cargo/bin:$PATH
export CARGO_BUILD_JOBS=2 RAYON_NUM_THREADS=2
mkdir -p /foss/pdks
tar -xf /build/pdk-models.tar -C /foss/pdks
cd /build/iverilog
sh autoconf.sh
./configure --prefix=/opt/iverilog --enable-libvvp
make -j2
make install
export PATH=/opt/iverilog/bin:$PATH
printf '/opt/iverilog/lib\n' > /etc/ld.so.conf.d/iverilog.conf
ldconfig
for version in 46 47; do
 if [ "$version" = 46 ]; then src=/build/ngspice; else src=/build/ngspice47; fi
 cd "$src"
 ./autogen.sh
 ./configure --prefix=/opt/ngspice-$version --without-x --enable-osdi --enable-xspice --enable-openmp --enable-klu --with-readline=yes CFLAGS='-O2 -g'
 make -j2
 make install
 /opt/ngspice-$version/bin/ngspice -v
done
cd /foss/pdks/ihp-sg13g2/libs.tech/verilog-a
for model in psp103 psp103_nqs r3_cmc mosvar; do
 directory=$model
 if [ "$model" = psp103_nqs ]; then directory=psp103; fi
 /build/OpenVAF-Reloaded/target/release/openvaf-r -D__NGSPICE__ --target_cpu generic -o ../ngspice/osdi/$model.osdi $directory/$model.va
 file ../ngspice/osdi/$model.osdi
done
