# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# Base system & build dependencies
# ------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        sudo \
        git \
        cmake \
        ninja-build \
        gperf \
        ccache \
        dfu-util \
        device-tree-compiler \
        wget \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        python3-tk \
        xz-utils \
        file \
        make \
        gcc \
        gcc-multilib \
        g++-multilib \
        libsdl2-dev \
        libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Python tooling (system Python, no venv)
# ------------------------------------------------------------
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir west

# ------------------------------------------------------------
# Zephyr SDK (legacy 0.17.x, for Zephyr 4.2/4.3 workspaces)
# ------------------------------------------------------------
# Zephyr versions pin their SDK in the zephyr tree's SDK_VERSION file
# (4.2 -> 0.17.2, 4.3 -> 0.17.4, 4.5 -> 1.0.1) and the workspace's
# find_package version range rejects an SDK outside its series. The
# image therefore carries both series: 0.17.4 (the newest 0.17.x) at
# /opt/zephyr-sdk-0.17.4 and 1.0.1 (current) as the default at
# /opt/zephyr-sdk. Both cmake packages are registered, so each
# workspace's range check selects the compatible SDK.
ARG ZEPHYR_SDK_LEGACY_VERSION=0.17.4
ENV ZEPHYR_SDK_LEGACY_DIR=/opt/zephyr-sdk-${ZEPHYR_SDK_LEGACY_VERSION}

RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_LEGACY_VERSION}/zephyr-sdk-${ZEPHYR_SDK_LEGACY_VERSION}_linux-x86_64.tar.xz && \
    mkdir -p ${ZEPHYR_SDK_LEGACY_DIR} && \
    tar -xf zephyr-sdk-${ZEPHYR_SDK_LEGACY_VERSION}_linux-x86_64.tar.xz -C ${ZEPHYR_SDK_LEGACY_DIR} --strip-components=1 && \
    rm zephyr-sdk-${ZEPHYR_SDK_LEGACY_VERSION}_linux-x86_64.tar.xz && \
    ${ZEPHYR_SDK_LEGACY_DIR}/setup.sh -t all -h -c

# ------------------------------------------------------------
# Zephyr SDK 1.0.1 (default, for Zephyr 4.5 workspaces)
# ------------------------------------------------------------
# SDK 1.0 changed the release format: the monolithic tarball is now
# the *_gnu bundle (all GNU cross toolchains) next to split per-arch
# assets, and host tools ship separately (this image installs cmake,
# ninja and dtc from apt above, per the image contract).
ARG ZEPHYR_SDK_VERSION=1.0.1
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk

RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_gnu.tar.xz && \
    mkdir -p ${ZEPHYR_SDK_INSTALL_DIR} && \
    tar -xf zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_gnu.tar.xz -C ${ZEPHYR_SDK_INSTALL_DIR} --strip-components=1 && \
    rm zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_gnu.tar.xz && \
    if [ -x ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh ]; then ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh -c; fi

ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=${ZEPHYR_SDK_INSTALL_DIR}

# ------------------------------------------------------------
# Zephyr Python requirements (AUTHORITATIVE)
# ------------------------------------------------------------
# We temporarily clone Zephyr only to install its Python deps,
# then remove it to keep the image clean.
#
# This guarantees compatibility with the pinned Zephyr versions and
# avoids guessing missing dependencies (jsonschema, pyelftools, etc.).
# Requirements for the current Zephyr (v4.5.0) and the legacy series
# still in service (v4.2.0) are both installed; the union is what
# workspaces of either series need.
# ------------------------------------------------------------
ARG ZEPHYR_VERSION=v4.5.0
ARG ZEPHYR_VERSION_LEGACY=v4.2.0

RUN git clone --depth 1 --branch ${ZEPHYR_VERSION} \
        https://github.com/zephyrproject-rtos/zephyr.git /tmp/zephyr && \
    python3 -m pip install --no-cache-dir \
        -r /tmp/zephyr/scripts/requirements.txt && \
    rm -rf /tmp/zephyr && \
    git clone --depth 1 --branch ${ZEPHYR_VERSION_LEGACY} \
        https://github.com/zephyrproject-rtos/zephyr.git /tmp/zephyr && \
    python3 -m pip install --no-cache-dir \
        -r /tmp/zephyr/scripts/requirements.txt && \
    rm -rf /tmp/zephyr

# ------------------------------------------------------------
# Beningo Zephyr AI skills
# ------------------------------------------------------------
# Jacob Beningo's Zephyr AI skills (build-doctor, devicetree-author,
# kconfig-tuner, renode-runner, zephyr-bsp-scaffold, plus the index)
# ship inside the image so agents and developers working in the
# container share one copy. Vendored under container/skills/beningo/;
# provenance is recorded in the index skill
# (beningo-zephyr-skills/SKILL.md).
COPY skills/beningo /opt/zephyr-skills/beningo
ENV WEST_ENV_SKILLS_DIR=/opt/zephyr-skills

# ------------------------------------------------------------
# Defaults
# ------------------------------------------------------------
WORKDIR /work
CMD ["/bin/bash"]
