#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 ElectroHire, Inc.
#
# Full environment test for a per-version zephyr-build-env image.
#
# Runs INSIDE the image with a west workspace mounted at /work. The
# workspace's Zephyr tree must match the image's Zephyr version (the
# image exports WEST_ENV_ZEPHYR_VERSION). For the workspace's Zephyr
# release, this test builds samples/bluetooth/peripheral — a sample
# chosen because it stresses the whole environment at once: the full
# Bluetooth host stack, devicetree, Kconfig, the cross toolchain, and
# sysbuild multi-image linking — twice:
#
#   debug    sysbuild + MCUboot, CONFIG_DEBUG_OPTIMIZATIONS + asserts
#   release  sysbuild + MCUboot, CONFIG_SPEED_OPTIMIZATIONS
#
# Each build must produce the MCUboot image and the imgtool-signed
# application binary; the signed binary proves the release's Python
# requirements (imgtool, cryptography, intelhex) actually work, not
# just install.
#
# Copyright handling: the sample is copied to scratch space inside
# the container and only the copy is adjusted (a sysbuild.conf and
# appended prj.conf lines). The workspace tree is never modified, and
# the sample's own copyright and SPDX headers travel with the copy
# untouched.
#
# Verdict: exit 0 and a FULLTEST_ALL_OK line when both builds pass;
# any failed step aborts with a non-zero exit (set -eu). Per-build
# markers: FULLTEST_DEBUG_OK / FULLTEST_RELEASE_OK with artifact
# sizes and sha256 values.
set -eu

TOPDIR="${FULLTEST_TOPDIR:-/work}"
BOARD="${FULLTEST_BOARD:-nrf52840dk/nrf52840}"
SAMPLE_REL="zephyr/samples/bluetooth/peripheral"
SCRATCH="/tmp/fulltest"

echo "== full-env-test =="
echo "image zephyr: ${WEST_ENV_ZEPHYR_VERSION:-unknown} sdk: ${WEST_ENV_ZEPHYR_SDK_VERSION:-unknown}"
echo "board: $BOARD  sample: $SAMPLE_REL  topdir: $TOPDIR"

test -d "$TOPDIR/.west" || { echo "FAIL: $TOPDIR is not a west workspace topdir (no .west)"; exit 1; }
test -d "$TOPDIR/$SAMPLE_REL" || { echo "FAIL: sample not found at $TOPDIR/$SAMPLE_REL"; exit 1; }

cd "$TOPDIR"
west --version
cmake --version | head -1
python3 --version
dtc --version | head -1
west zephyr-export

build_one() {
    kind="$1"
    app="$SCRATCH/app-$kind"
    bdir="$SCRATCH/build-$kind"
    rm -rf "$app" "$bdir"
    mkdir -p "$SCRATCH"
    cp -r "$TOPDIR/$SAMPLE_REL" "$app"
    printf 'SB_CONFIG_BOOTLOADER_MCUBOOT=y\n' > "$app/sysbuild.conf"
    if [ "$kind" = "debug" ]; then
        printf '\n# west-env full-env-test: debug build adjustments (scratch copy only)\nCONFIG_DEBUG_OPTIMIZATIONS=y\nCONFIG_ASSERT=y\n' >> "$app/prj.conf"
    else
        printf '\n# west-env full-env-test: release build adjustments (scratch copy only)\nCONFIG_SPEED_OPTIMIZATIONS=y\n' >> "$app/prj.conf"
    fi
    echo "== building $kind (sysbuild + MCUboot) =="
    west build --sysbuild -p always -b "$BOARD" -d "$bdir" "$app"
    mcuboot_img="$(find "$bdir" -path '*mcuboot*' -name 'zephyr.bin' | head -1)"
    signed_bin="$(find "$bdir" -name 'zephyr.signed.bin' | head -1)"
    app_elf="$(find "$bdir" -name 'zephyr.elf' -not -path '*mcuboot*' | head -1)"
    test -n "$mcuboot_img" || { echo "FAIL: no MCUboot image in $bdir"; exit 1; }
    test -n "$signed_bin" || { echo "FAIL: no signed application binary in $bdir"; exit 1; }
    test -n "$app_elf" || { echo "FAIL: no application ELF in $bdir"; exit 1; }
    echo "mcuboot: $mcuboot_img ($(wc -c < "$mcuboot_img") bytes, sha256 $(sha256sum "$mcuboot_img" | cut -d' ' -f1))"
    echo "signed:  $signed_bin ($(wc -c < "$signed_bin") bytes, sha256 $(sha256sum "$signed_bin" | cut -d' ' -f1))"
    upper="$(printf '%s' "$kind" | tr '[:lower:]' '[:upper:]')"
    echo "FULLTEST_${upper}_OK board=$BOARD"
}

build_one debug
build_one release

echo "FULLTEST_ALL_OK zephyr=${WEST_ENV_ZEPHYR_VERSION:-unknown} board=$BOARD sample=samples/bluetooth/peripheral"
