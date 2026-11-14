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
# Zephyr SDK (exactly one, pinned to the image's Zephyr version)
# ------------------------------------------------------------
# Images are built per Zephyr version (see build-matrix.sh): each
# image carries exactly the SDK that its Zephyr release pins in the
# zephyr tree's SDK_VERSION file, because a workspace's find_package
# version range rejects an SDK outside its series, and each release's
# Python requirements differ. Supported pins:
#   Zephyr 4.0.0 / 4.1.0 -> SDK 0.17.0
#   Zephyr 4.2.0         -> SDK 0.17.2
#   Zephyr 4.3.0         -> SDK 0.17.4
#   Zephyr 4.4.0 / 4.5.0 -> SDK 1.0.1
# The 0.x series ships as one monolithic tarball with setup.sh; the
# 1.x series ships as a *_gnu bundle (all GNU cross toolchains) next
# to split per-arch assets, with host tools separate (this image
# installs cmake, ninja and dtc from apt above, per the contract).
ARG ZEPHYR_SDK_VERSION=1.0.1
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk

RUN case "${ZEPHYR_SDK_VERSION}" in \
      0.*) \
        wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz && \
        mkdir -p ${ZEPHYR_SDK_INSTALL_DIR} && \
        tar -xf zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz -C ${ZEPHYR_SDK_INSTALL_DIR} --strip-components=1 && \
        rm zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz && \
        ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh -t all -h -c ;; \
      *) \
        wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_gnu.tar.xz && \
        mkdir -p ${ZEPHYR_SDK_INSTALL_DIR} && \
        tar -xf zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_gnu.tar.xz -C ${ZEPHYR_SDK_INSTALL_DIR} --strip-components=1 && \
        rm zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_gnu.tar.xz && \
        if [ -x ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh ]; then ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh -c; fi ;; \
    esac

ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=${ZEPHYR_SDK_INSTALL_DIR}

# ------------------------------------------------------------
# Zephyr Python requirements (AUTHORITATIVE)
# ------------------------------------------------------------
# We temporarily clone the image's pinned Zephyr release only to
# install its Python deps, then remove it to keep the image clean.
#
# This guarantees compatibility with the pinned Zephyr version and
# avoids guessing missing dependencies (jsonschema, pyelftools, etc.).
# ------------------------------------------------------------
ARG ZEPHYR_VERSION=v4.5.0

RUN git clone --depth 1 --branch ${ZEPHYR_VERSION} \
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

# Per-version skills overlay: the five skills are version-agnostic
# across Zephyr 4.x except for the facts in the overlay for this
# image's exact Zephyr release (its SDK pin and series, the toolchain
# form, the requirements source). Every overlay ships in the image;
# the one matching ZEPHYR_VERSION is selected at build time and
# copied to version-overlay.md, which agents read before the skills.
COPY skills/version-overlays /opt/zephyr-skills/version-overlays
RUN cp "/opt/zephyr-skills/version-overlays/$(echo "${ZEPHYR_VERSION}" | sed 's/^v//').md" \
       /opt/zephyr-skills/version-overlay.md
ENV WEST_ENV_ZEPHYR_VERSION=${ZEPHYR_VERSION}
ENV WEST_ENV_ZEPHYR_SDK_VERSION=${ZEPHYR_SDK_VERSION}

# ------------------------------------------------------------
# Defaults
# ------------------------------------------------------------
WORKDIR /work
CMD ["/bin/bash"]
