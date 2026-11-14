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
#   ghcr.io/bitconcepts/zephyr-build-env:<zephyr>-sdk<sdk>-ubuntu22.04
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

REGISTRY=ghcr.io/bitconcepts/zephyr-build-env
UBUNTU_VERSION=22.04

# Zephyr version -> SDK version (from each release's SDK_VERSION file)
matrix="
4.0.0 0.17.0
4.1.0 0.17.0
4.2.0 0.17.2
4.3.0 0.17.4
4.4.0 1.0.1
4.5.0 1.0.1
"

if [ "${1:-}" = "--list" ]; then
    printf '%s\n' "$matrix" | while read -r z s; do
        [ -n "$z" ] && echo "$z -> SDK $s -> $REGISTRY:$z-sdk$s-ubuntu$UBUNTU_VERSION"
    done
    exit 0
fi

want="${1:-}"

printf '%s\n' "$matrix" | while read -r zephyr sdk; do
    [ -n "$zephyr" ] || continue
    if [ -n "$want" ] && [ "$want" != "$zephyr" ]; then
        continue
    fi
    tag="$REGISTRY:$zephyr-sdk$sdk-ubuntu$UBUNTU_VERSION"
    echo "=== building $tag (Zephyr $zephyr, SDK $sdk) ==="
    docker build \
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
