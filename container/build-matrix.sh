#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
#
# Build the per-Zephyr-version zephyr-build-env images.
#
# One image per supported Zephyr release, each carrying exactly the
# SDK that release pins (its SDK_VERSION file) and exactly that
# release's Python requirements. A workspace selects its image in
# west-env.yml (env.image), so the version grain is the image tag:
#
#   ghcr.io/electrohire/zephyr-build-env:<zephyr>-sdk<sdk>-ubuntu<ubuntu>
#
# The Ubuntu suffix follows the base image that version needs (see
# the matrix below): 22.04 for Zephyr 4.0-4.3, 24.04 for 4.4/4.5.
#
# Usage:
#   ./build-matrix.sh              build every supported version
#   ./build-matrix.sh 4.2.0        build one version
#   ./build-matrix.sh --list       print the supported matrix
#
# The dual-SDK image built by build.sh remains valid; this matrix is
# the hermetic per-version set that supersedes it.
set -eu

cd "$(dirname "$0")"

REGISTRY=ghcr.io/electrohire/zephyr-build-env

# Zephyr version -> SDK version -> Ubuntu base. SDK pins come from
# each release's SDK_VERSION file. The Ubuntu base is the oldest whose
# apt packages meet that release's getting-started minimums (CMake /
# Python): 4.0-4.3 need CMake >= 3.20.5 and Python >= 3.10 (22.04);
# 4.4 needs Python >= 3.12 and 4.5 needs CMake >= 3.28 and
# Python >= 3.12 (24.04). The tag suffix follows the base.
matrix="
4.0.0 0.17.0 22.04
4.1.0 0.17.0 22.04
4.2.0 0.17.2 22.04
4.3.0 0.17.4 22.04
4.4.0 1.0.1 24.04
4.5.0 1.0.1 24.04
"

if [ "${1:-}" = "--list" ]; then
    printf '%s\n' "$matrix" | while read -r z s u; do
        if [ -n "$z" ]; then echo "$z -> SDK $s -> Ubuntu $u -> $REGISTRY:$z-sdk$s-ubuntu$u"; fi
    done
    exit 0
fi

want="${1:-}"

printf '%s\n' "$matrix" | while read -r zephyr sdk ubuntu; do
    [ -n "$zephyr" ] || continue
    if [ -n "$want" ] && [ "$want" != "$zephyr" ]; then
        continue
    fi
    tag="$REGISTRY:$zephyr-sdk$sdk-ubuntu$ubuntu"
    echo "=== building $tag (Zephyr $zephyr, SDK $sdk, Ubuntu $ubuntu) ==="
    docker build \
        --build-arg BASE_IMAGE="ubuntu:$ubuntu" \
        --build-arg ZEPHYR_VERSION="v$zephyr" \
        --build-arg ZEPHYR_SDK_VERSION="$sdk" \
        -t "$tag" \
        .
done

if [ -n "$want" ]; then
    printf '%s\n' "$matrix" | grep -q "^$want " || {
        echo "ERROR: Zephyr $want is not in the supported matrix (try --list)" >&2
        exit 1
    }
fi
