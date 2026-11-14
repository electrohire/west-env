---
name: beningo-zephyr-skills
description: Standing pointer to Jacob Beningo's Zephyr AI skills, adopted for every Zephyr project by the owner's order (2026-11-06). Use whenever work touches a Zephyr firmware project (currently the iSMART control board and fanout board firmware from tristen-laptop): load the matching beningo-* skill before devicetree, Kconfig, BSP, build-diagnosis, or simulation work.
---

# Beningo Zephyr AI Skills (adopted 2026-11-06)

The owner directed: use Jacob Beningo's Zephyr AI skills on any project that uses Zephyr. Current Zephyr projects: the Inductoheat iSMART control board firmware and fanout board firmware (both run from tristen-laptop, never the desktop).

## The five skills (siblings of this directory)

- beningo-zephyr-bsp-scaffold: generate the BSP four-file skeleton (devicetree, Kconfig.<board>, defconfig, pinctrl) from a known-good reference board, with existence and reference self-checks.
- beningo-devicetree-author: devicetree edits where every new node or property cites the actual Zephyr binding YAML; no hallucinated register addresses.
- beningo-kconfig-tuner: plain-English goal to a minimal verified CONFIG_* diff; every symbol grep-verified in the Zephyr tree first (grep-or-refuse), dependencies checked.
- beningo-build-doctor: classify a Zephyr build failure into one of five categories (missing binding, wrong overlay, Kconfig conflict, linker issue, pinmux clash) before fixing.
- beningo-renode-runner: validate firmware end-to-end under Renode simulation when hardware is not available.

## Per-version overlay (west-env container images)

The five skills are version-agnostic across Zephyr 4.x except for a small set of version facts: each release pins its own SDK (4.0.0/4.1.0 pin 0.17.0, 4.2.0 pins 0.17.2, 4.3.0 pins 0.17.4, 4.4.0/4.5.0 pin 1.0.1), the SDK install form changes with the series (0.x monolithic tarball, 1.x GNU bundle), and symbols and bindings drift between releases. Inside a west-env per-version image, read /opt/zephyr-skills/version-overlay.md before using a skill: it is the overlay for that image's exact Zephyr version, selected at image build time from container/skills/version-overlays/ in the west-env repo, and it overrides any conflicting assumption in a skill. Outside the container images there is no overlay; verify version facts against the workspace's own Zephyr tree instead.

## Provenance

Jacob's official distribution is email-gated for Embedded Bytes subscribers (beningo.com/zephyr-ai-skills); there is no official public repo. This local copy was vendored 2026-11-06 from github.com/AnkyXCoder/zephyr-mcp-server (skills/ directory), whose five skill texts match Jacob's published method in his articles (the kconfig-tuner grep-or-refuse workflow verbatim in substance). If the owner forwards his official subscriber bundle, replace these files with the official ones verbatim and update this note.

## Precedence

Where a skill conflicts with the target repo's AGENTS.md, the program's protected-file locks, or the owner's standing orders (flash discipline, board verification, no-flash-without-orders), the repo rules and the owner's orders govern. renode-runner results are simulation evidence only and never substitute for on-hardware verdicts.
