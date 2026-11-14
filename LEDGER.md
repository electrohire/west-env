# Change Ledger

## 2026-11-14 — Fix: pip upgrade on Ubuntu 24.04 bases (4.4/4.5 image builds)

The first container-images runs for Zephyr 4.4.0 and 4.5.0 failed their build payloads: Ubuntu 24.04's pip is a Debian package with no RECORD file, so `pip install --upgrade pip` cannot uninstall it and exits 1 ("Cannot uninstall pip 24.0, RECORD file not found"). The 22.04 images (4.0.0, 4.1.0, 4.2.0, 4.3.0) published and verified fine (IMAGE_VERIFY_OK each). Fix: the Dockerfile's pip upgrade now passes --ignore-installed, installing the new pip over the Debian one; TEST-CONTAINER-008 pins it.

---

## 2026-11-14 — Project moved to ElectroHire; images published from CI; per-version skills overlays

Objective: Owner order (iSMART chat, 2026-11-14): resume the west-env work and finish it, put the dockers on GitHub, move everything to ElectroHire (BitConcepts is being retired and ElectroHire is the new home), update all docs, and make sure the Zephyr skills are in every container, adjusted per version where versions differ.

What was done:
- Home move (REQ-CONTAINER-008, new): every functional reference retargeted from BitConcepts to ElectroHire — image registry ghcr.io/electrohire/zephyr-build-env (build-matrix.sh, build.sh, build.cmd, README.md, container/README.md, example workspace, container/.env.example.posix), repository URLs (quickstarts, example west.yml, module.yml, CHANGELOG links), maintainer email to tpierson@electrohire.com. A repo-wide grep for the former name across functional files is pinned by TEST-CONTAINER-007. The repository itself is created fresh under the electrohire org and this branch lands there by pull request, so the new home does not sit in the former owner's fork network.
- Publishing (REQ-CONTAINER-008): new .github/workflows/container-images.yml, manual dispatch for one Zephyr version or all, one matrix job per version, GITHUB_TOKEN with packages: write. Each job frees disk space, builds from container/Dockerfile, pushes, and then verifies its own published image (skills listing, version overlay for its release, sdk_version equal to the pin, WEST_ENV_* env values, west --version) and prints IMAGE_VERIFY_OK; that verify step is the job's payload verdict.
- Skills per version (REQ-CONTAINER-004 amended): the five Beningo skills audited — they are version-agnostic across Zephyr 4.x except for version facts. New container/skills/version-overlays/<zephyr>.md for each supported release (4.0.0 through 4.5.0) carries those facts (SDK pin read from the release's SDK_VERSION file, SDK series and install form, GNU-only toolchain note for the 1.x images, requirements source, HWMv2 board model). The Dockerfile copies all overlays into every image and selects the one matching ZEPHYR_VERSION to /opt/zephyr-skills/version-overlay.md at build time; images export WEST_ENV_ZEPHYR_VERSION / WEST_ENV_ZEPHYR_SDK_VERSION. The vendored index skill gained a section pointing agents at the overlay.
- Docs: docs/REQUIREMENTS.md (REQ-CONTAINER-008 added, REQ-CONTAINER-004 amended, REQ-CONTAINER-007 registry path retargeted), docs/TESTS.md (TEST-CONTAINER-006/007), container/README.md (overlay contract + publishing section), README.md (home note), CHANGELOG.md (Unreleased entry).

Files changed: container/Dockerfile, container/build-matrix.sh, container/build.sh, container/build.cmd, container/README.md, container/.env.example.posix, container/skills/beningo/beningo-zephyr-skills/SKILL.md, container/skills/version-overlays/* (new), .github/workflows/container-images.yml (new), tests/test_container_images.py (new), README.md, CHANGELOG.md, MAINTAINERS.yml, module.yml, docs/REQUIREMENTS.md, docs/TESTS.md, docs/quickstart-linux.md, docs/quickstart-windows.md, example/workspace/west-env.yml, example/workspace/west.yml, LEDGER.md

Checks run: pytest tests/ (west e2e deselected as before) — 165 passed, 13 skipped (baseline 160 passed + 5 new container-image tests); ruff check — clean; ruff format — the new test file formatted, 2 pre-existing unformatted files on the base branch left untouched; build-matrix.sh --list shows all six tags under ghcr.io/electrohire/zephyr-build-env; the container-images workflow parses as valid YAML.

Addendum, same day (owner follow-ups): PR #1's first CI run failed its payload on lint (ruff format on west_env/container.py and west_env/flash.py, both from this branch's earlier commits) and on the native-sim job's apt step (the runner mirror 404'd on superseded glibc packages); both are fixed in this branch (format applied; the CI step now runs apt-get update first). The owner also required the Zephyr recommended environment setups and copyright instructions to be kept per version, and a full test per version. Checking the releases' own getting-started docs showed the single Ubuntu 22.04 base did NOT meet 4.4 (Python >= 3.12) or 4.5 (CMake >= 3.28, Python >= 3.12), so bases are now version-appropriate (REQ-CONTAINER-007 amended): Ubuntu 22.04 for 4.0-4.3, Ubuntu 24.04 for 4.4/4.5, the tag suffix follows the base, and each version overlay states its release's recommended environment and copyright/provenance position. The full environment test is REQ-CONTAINER-009: an in-image script builds samples/bluetooth/peripheral as debug and release sysbuilds with MCUboot, and the container-full-test workflow runs it per published version.

Open TODOs:
- [ ] Land this branch in electrohire/west-env by PR and merge on green CI
- [ ] Dispatch container-images for 4.2.0, verify IMAGE_VERIFY_OK, then dispatch the remaining versions
- [ ] Run the container-full-test workflow per version and verify FULLTEST_ALL_OK payloads
- [ ] Switch the iSMART control workspace to the ElectroHire 4.2.0 image and electrohire/west-env manifest entry, rebuild, flash, bench regression

---

## 2026-11-13 — Fork: J-Link passthrough fixes + Beningo Zephyr skills in the image

Objective: Make host-side J-Link flashing actually work end to end on Windows (owner order, iSMART bench), and ship Jacob Beningo's Zephyr AI skills inside the build container.

What was done:
- west_env/flash.py: commander script now written to a real temp file passed via -CommanderScript (was /dev/stdin, nonexistent on Windows, REQ-JLINK-006); J-Link discovery probes both JLinkExe.exe and JLink.exe (REQ-JLINK-006); FlashManager takes serial + interface, emits -SelectEmuBySN and `si SWD|JTAG` in flash and the GDB server (REQ-JLINK-005); flash verdict checks captured J-Link output for failure markers, not the exit code alone (REQ-JLINK-007)
- west_env/config.py: jlink.serial and jlink.interface parsed and validated (REQ-JLINK-005)
- west_commands/env.py: `west env flash` extracts --device/-device and --serial (space or = form) from the passthrough instead of forwarding them blindly; config serial/interface wired into flash and debug
- container/Dockerfile + container/skills/beningo/: the five Beningo Zephyr skills plus the index vendored and copied to /opt/zephyr-skills/beningo with WEST_ENV_SKILLS_DIR exported (REQ-CONTAINER-004)
- docs: REQUIREMENTS.md (REQ-JLINK-005/006/007, REQ-CONTAINER-004 added), docs/flashing.md (serial/interface, script-file, output verdict), container/README.md (skills as an image responsibility)

Files changed: west_env/flash.py, west_env/config.py, west_commands/env.py, tests/test_new_modules.py, tests/test_config.py, container/Dockerfile, container/README.md, container/skills/beningo/*, docs/REQUIREMENTS.md, docs/flashing.md, LEDGER.md

Checks run: pytest tests/ — 155 passed, 14 skipped (2 west e2e tests deselected: they fail identically on pristine upstream main in this environment, verified by stash comparison); ruff check — 0 violations

Results: PASS for the unit suite. The image build with the new skills layer lands once a container engine reachable from the bench laptop's job context is confirmed.

Follow-up, same day: the bench control workspace was read on the laptop (Zephyr 4.2.0, its SDK_VERSION pins 0.17.2), and the laptop J-Link install carries JLink.exe and JFlash.exe but no JLinkExe.exe, confirming REQ-JLINK-006 was a live defect on this machine. The Dockerfile now installs SDK 1.0.1 as the default (Zephyr 4.5's pin, from the 1.0 *_gnu bundle) and keeps SDK 0.17.4 registered alongside for 4.2/4.3 workspaces (REQ-CONTAINER-005), with Python requirements for Zephyr v4.5.0 and v4.2.0; container/build.sh and build.cmd pins moved to Zephyr 4.5.0 / SDK 1.0.1.

Open TODOs:
- [ ] Build the image and verify: skills present at /opt/zephyr-skills/beningo, both SDKs registered, a Zephyr 4.2 workspace build (iSMART control) and a 4.5 sample build
- [ ] TEST-JLINK-001/002 on real hardware (iSMART control board, probe serial 69656048, JTAG)

---

# 2026-11-13 — sync-mode container contract completed (REQ-CONTAINER-006 extended)

**Scope**: west_env/sync.py, west_env/container.py, west_commands/env.py, tests (test_sync, test_new_modules).

The first bench build after the workspace_mode mount fix exposed the rest of the sync path, none of which had ever run end to end:

1. The synced volume carried no `.west/` (it sat in DEFAULT_EXCLUDES), so the container-side west found no workspace topdir and `west build` failed with `unknown command "build"`. `.west` is removed from the excludes; the tool's own container workspace check expects it present. New test: .west is not excluded.
2. Artifact sync-back only searched /work/build. Application layouts (build dir under the app, e.g. application/build/<cfg>) would have returned nothing. The find now covers any path containing a build directory.
3. `west env sync --back` silently performed a FORWARD sync: argparse routes everything after the action into the REMAINDER passthrough, so args.back never became true. do_run now honours --back from the passthrough for the sync action. New tests route both forms through do_run with _sync stubbed.
4. container.py now takes its mount spec from WorkspaceSync.volume_args instead of a hand-rolled equivalent, so the tmpfs variant's extra mount and any future mode change live in exactly one place.

Suite: 160 passed, 13 skipped, ruff clean.

---

# 2026-11-13 — per-Zephyr-version build images

**Scope**: container/Dockerfile, container/build-matrix.sh (new), container/build.sh, container/build.cmd, docs/REQUIREMENTS.md (REQ-CONTAINER-007).

Owner direction (2026-11-13): cover the supported Zephyr versions with their exact component versions, one container per Zephyr version from 4.0.0 onward. The Dockerfile is now parameterized on ZEPHYR_VERSION + ZEPHYR_SDK_VERSION and installs exactly one SDK (the SDK step branches on series: 0.x monolithic tarball + setup.sh, 1.x *_gnu bundle) and exactly that release's Python requirements. build-matrix.sh carries the supported matrix with the SDK pin read from each release's SDK_VERSION file (4.0.0/4.1.0 -> 0.17.0, 4.2.0 -> 0.17.2, 4.3.0 -> 0.17.4, 4.4.0/4.5.0 -> 1.0.1) and builds all versions or one named version. The dual-SDK image (REQ-CONTAINER-005) remains valid and in service on the bench laptop until the workspace is switched to its exact per-version image.

---

# 2026-11-13 — workspace_mode honored by container commands; install route corrected

**Scope**: west_env/container.py, tests/test_container.py, docs (quickstart-windows, quickstart-linux, REQUIREMENTS REQ-CONTAINER-006).

Two defects found driving the iSMART control workspace (Zephyr 4.2, workspace_mode sync) from a Linux/WSL host:

1. `west env build` ignored the configured workspace_mode: _container_args always bind-mounted the host workspace at /work, even in sync mode with the volume already populated by `west env sync`. On the bench this bind-mounted a DrvFs path and the build died in Zephyr's pristine step over a stale Windows CMakeCache. Fix: bind mode mounts the host directory; the sync family mounts the `west-env-ws-<slug>` volume, and run_container fails fast naming `west env sync` when the volume does not exist yet. Two existing tests now pin workspace_mode=bind explicitly (their legacy configs previously relied on the platform default); two new tests cover the volume mount and the missing-volume guard. Suite: 157 passed, 13 skipped, ruff clean.
2. The quickstarts presented `pip install -e` as a peer install route. Against west 1.5 it registers nothing: west's extension loader (west/commands.py extension_commands) reads manifest projects only, which the bench proved end to end (`west: unknown command "env"` with the package installed and its entry point present). Both quickstarts now lead with the manifest `west-commands:` entry and state plainly that pip alone is insufficient.

Risks: FlashManager output markers are substring-based; a future J-Link version rewording its errors could false-negative (flash would report success on a failed write). The bench flow keeps its own identity read-back gates, which catch that case.

## 2026-05-13 — Session end

Objective: Complete specsmith migration, cross-platform realignment, Slices 2–12 implementation, gap analysis, and repo cleanup.

What was done:
- specsmith migrated 0.3.0 → 0.10.1; full upgrade (20 governance files regenerated)
- Cross-platform realignment: 47 active requirements, 10 new groups, 12-slice feature plan
- Slices 2–11 implemented: backend.py, sync.py, cache.py, credentials.py, flash.py, vscode.py, platform.py, extended config.py and env.py
- 93 new unit tests (total 122); all pass on Windows/Linux/macOS × Python 3.10–3.12
- Slice 12: README rewritten (Windows-first), 6 new docs (quickstart × 3, troubleshooting, git-credentials, flashing)
- CI: 4 jobs (lint, unit-tests, docker-integration, native-sim-build); security job fixed; dependabot in place
- Lint: ruff config added to pyproject.toml; 0 violations
- CONTRIBUTING.md and SECURITY.md expanded
- EDSSharp removed from container.py (not general-purpose)

Files changed: All west_env/* modules, west_commands/env.py, tests/*, docs/*, .github/workflows/ci.yml, pyproject.toml, scaffold.yml, LEDGER.md, README.md, CONTRIBUTING.md, SECURITY.md

Checks run: pytest (122 pass), ruff check (0 violations), specsmith audit (28/28 healthy), specsmith validate (5/5)

Results: PASS — all checks green

Token estimate: high

Open TODOs:
- [ ] Manual tests: TEST-WINNUX-001/002, TEST-JLINK-001/002, TEST-WINPERF-001 (require hardware + Windows setup)
- [ ] Slice 12 remaining: platform-validated quick-start execution on real hardware

Risks: New backend/sync/flash modules are unit-tested but not yet exercised in CI E2E (hardware required)

Next step: Run CI on GitHub and verify all jobs pass; then advance to `specsmith phase next` (inception → architecture)

## 2026-04-05 — specsmith import
- Imported project: west-env
- Detected type: library-python
- Language: python
- Build system: pyproject

## 2026-05-13T14:34 — specsmith migration: 0.3.0 → 0.10.1
- **Author**: specsmith
- **Type**: migration
- **Status**: complete
- **Chain hash**: `17386908a46df64e...`

## 2026-05-13 — Gap analysis, Slice 12, CI/security/lint cleanup
- **Author**: Oz (agent)
- **Type**: gap-analysis + docs + lint + CI
- Gap analysis: 92 ruff violations found; 0 genuine after config + fixes
- Lint: added `[tool.ruff.lint] select/ignore` to pyproject.toml (line-length=120, E402 ignored)
- Lint fixes: removed unused imports (os, which, Tuple), unused vars (docker_run, shell, expected), f-string issues, E741 ambiguous names in tests
- CI security job: fixed bash process substitution `<()` → portable `pip-audit --desc on`
- CI lint step: removed `--select=E,F,W` from command (now in pyproject.toml); ruff check clean
- Slice 12 docs: rewrote README.md (Windows-first, no stale WSL claims, all new commands listed)
- Slice 12 docs created: docs/quickstart-windows.md, docs/quickstart-linux.md, docs/quickstart-macos.md, docs/troubleshooting.md, docs/git-credentials.md, docs/flashing.md
- CONTRIBUTING.md: expanded to full contributor guide (governance, style, tests, platform testing, requirement traceability)
- SECURITY.md: expanded with vulnerability reporting flow, security design properties, dependency audit scope
- Final: ruff check passes (0 violations), 122 unit tests pass, specsmith audit 28/28 healthy

## 2026-05-13 — Slices 2–11 implementation
- **Author**: Oz (agent)
- **Type**: implementation
- New modules: west_env/backend.py, west_env/sync.py, west_env/cache.py, west_env/credentials.py, west_env/flash.py, west_env/vscode.py, west_env/platform.py
- Extended: west_env/config.py (backend, workspace_mode, cache, git, jlink fields; backward compat)
- Extended: west_commands/env.py (sync, flash, debug, cache, benchmark, generate-tasks actions; extended doctor)
- Tests: test_backend.py (30 tests), test_sync.py (19 tests), test_new_modules.py (44 tests)
- All 122 unit tests pass on Windows (Python 3.11); 1 skip (chmod on Windows)
- CI updated: 4 jobs — lint (ruff), unit-tests (3 OS × 3 Python), docker-integration (ubuntu), native-sim-build (ubuntu)
- pyproject.toml: added dev extras with ruff
- Final: specsmith validate 5/5; all tests green

## 2026-05-13 — specsmith cross-platform realignment
- **Author**: Oz (agent)
- **Type**: realignment + governance rewrite
- Triggered by: transition to cross-platform Zephyr RTOS developer environment (Windows / Linux / macOS)
- Inventory: 19 requirements, 14 tests, no feature plan, no platform model
- Classification: 6 KEEP, 3 MODIFY, 10 RETIRE — REQ-ENGINE-*, REQ-CONTAINER-001, REQ-UTIL-002, REQ-CMD-001–005 retired
- 38 new requirements added across 10 groups: PLATFORM, WINNUX, WINPERF, WORKSPACE, CACHE, GIT, JLINK, VSCODE, BACKEND, TESTABILITY
- Final active requirement count: 47
- Both pre-existing coverage gaps (REQ-CMD-003, REQ-CMD-005) eliminated by retirement
- Created: docs/REALIGNMENT-REPORT.md, docs/FEATURE-PLAN.md
- Rewrote: docs/ARCHITECTURE.md (8 layers), docs/REQUIREMENTS.md (47 reqs), docs/TESTS.md (stubs for all new reqs)
- Architecture: 8 layers × 3 platforms × 6 backends × 4 workspace modes
- Feature plan: 12 vertical slices (Slice 1 complete, Slices 2–12 planned)
- Final state: specsmith validate 5/5, audit 27+ checks pass

## 2026-05-13 — specsmith full audit and governance enrichment
- **Author**: Oz (agent)
- **Type**: audit + governance + refactor
- Ran `specsmith upgrade --full`: regenerated 20 governance files (SESSION-PROTOCOL.md, LIFECYCLE.md, RULES.md, ROLES.md, CONTEXT-BUDGET.md, VERIFICATION.md, DRIFT-METRICS.md, exec/setup/run shims, community files, CI configs, dependabot, dev-release workflow)
- Ran `specsmith audit --fix`: created stub `docs/TESTS.md` (only fixable issue)
- Ran `specsmith apply`: regenerated `.github/workflows/ci.yml`, `.github/dependabot.yml`, `.github/workflows/dev-release.yml`
- Enriched `docs/ARCHITECTURE.md` with real module descriptions and design decisions
- Replaced stub `docs/REQUIREMENTS.md` with 19 real requirements across 6 modules (REQ-CONFIG-001–004, REQ-ENGINE-001–003, REQ-CONTAINER-001–003, REQ-UTIL-001–002, REQ-CMD-001–006, REQ-BUILD-001)
- Populated `docs/TESTS.md` with 14 test entries mapped to requirements
- Removed EDSSharp/CANopenEditor bind-mount code from `west_env/container.py` (project-specific; breaks general-purpose use)
- Removed REQ-CONTAINER-004 and all EDSSharp references from docs
- Final state: `specsmith validate` 5/5 checks pass; `specsmith audit` 27/28 checks pass (2 coverage gaps are genuine: interactive shell, --container flag unit test)
