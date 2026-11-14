"""Source-level tests for the per-version container images.

These tests pin the ElectroHire home of the project (REQ-CONTAINER-008):
the image registry namespace, the per-version skills overlays
(REQ-CONTAINER-004 as amended), and the GHCR publishing workflow.
They read repository files only; the images themselves are built and
verified by .github/workflows/container-images.yml.
"""

# SPDX-License-Identifier: Apache-2.0

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONTAINER_DIR = REPO_ROOT / "container"


def _matrix_rows():
    """Parse the Zephyr -> (SDK, Ubuntu) matrix out of build-matrix.sh."""
    text = (CONTAINER_DIR / "build-matrix.sh").read_text(encoding="utf-8")
    found = re.findall(r"^(\d+\.\d+\.\d+) (\d+\.\d+\.\d+) (\d+\.\d+)$", text, re.M)
    return {zephyr: (sdk, ubuntu) for zephyr, sdk, ubuntu in found}


def _matrix_pairs():
    return {(z, sdk) for z, (sdk, _u) in _matrix_rows().items()}


# Each release's getting-started minimums (CMake, Python), verified
# from that release's own doc/develop/getting_started/index.rst, and
# the Ubuntu base whose apt packages meet them.
VERSION_MINIMUMS = {
    "4.0.0": ("3.20.5", "3.10", "22.04"),
    "4.1.0": ("3.20.5", "3.10", "22.04"),
    "4.2.0": ("3.20.5", "3.10", "22.04"),
    "4.3.0": ("3.20.5", "3.10", "22.04"),
    "4.4.0": ("3.20.5", "3.12", "24.04"),
    "4.5.0": ("3.28.0", "3.12", "24.04"),
}


class ContainerImageTests(unittest.TestCase):
    def test_matrix_registry_is_electrohire(self):
        text = (CONTAINER_DIR / "build-matrix.sh").read_text(encoding="utf-8")
        self.assertIn("ghcr.io/electrohire/zephyr-build-env", text)
        self.assertNotIn("bitconcepts", text.lower())

    def test_every_matrix_version_has_a_skills_overlay(self):
        pairs = _matrix_pairs()
        self.assertGreaterEqual(len(pairs), 6)
        overlays = CONTAINER_DIR / "skills" / "version-overlays"
        for zephyr, sdk in pairs:
            overlay = overlays / f"{zephyr}.md"
            self.assertTrue(overlay.is_file(), f"missing overlay for {zephyr}")
            body = overlay.read_text(encoding="utf-8")
            self.assertIn(f"Zephyr {zephyr}", body)
            self.assertIn(sdk, body)

    def test_dockerfile_ships_skills_and_selects_version_overlay(self):
        dockerfile = (CONTAINER_DIR / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY skills/beningo /opt/zephyr-skills/beningo", dockerfile)
        self.assertIn("COPY skills/version-overlays", dockerfile)
        self.assertIn("/opt/zephyr-skills/version-overlay.md", dockerfile)
        self.assertIn("WEST_ENV_SKILLS_DIR=/opt/zephyr-skills", dockerfile)
        self.assertIn("ENV WEST_ENV_ZEPHYR_VERSION=", dockerfile)
        self.assertIn("ENV WEST_ENV_ZEPHYR_SDK_VERSION=", dockerfile)

    def test_functional_files_have_no_bitconcepts_references(self):
        # Prose history may name the former home (the CHANGELOG records
        # the move); what is pinned is that no reference still points
        # there: no registry path, repo URL, mail domain, or namespace.
        forbidden = [
            "ghcr.io/bitconcepts",
            "github.com/bitconcepts",
            "bitconcepts/zephyr-build-env",
            "@bitconcepts.tech",
            'image_namespace="bitconcepts"',
            "image_namespace=bitconcepts",
        ]
        functional = [
            "README.md",
            "CHANGELOG.md",
            "MAINTAINERS.yml",
            "module.yml",
            "container/README.md",
            "container/build.sh",
            "container/build.cmd",
            "container/build-matrix.sh",
            "container/.env.example.posix",
            "docs/REQUIREMENTS.md",
            "docs/quickstart-linux.md",
            "docs/quickstart-windows.md",
            "example/workspace/west-env.yml",
            "example/workspace/west.yml",
        ]
        for rel in functional:
            body = (REPO_ROOT / rel).read_text(encoding="utf-8").lower()
            for needle in forbidden:
                self.assertNotIn(needle, body, f"{rel} still references the former home: {needle}")

    def test_base_image_is_version_appropriate(self):
        # REQ-CONTAINER-007 as amended: the base is the oldest Ubuntu
        # whose apt packages meet the release's getting-started
        # minimums; 4.4 needs Python 3.12 and 4.5 needs CMake 3.28, so
        # both ride Ubuntu 24.04 while 4.0-4.3 stay on 22.04.
        rows = _matrix_rows()
        self.assertEqual(set(rows), set(VERSION_MINIMUMS))
        for zephyr, (_cmake, _python, ubuntu) in VERSION_MINIMUMS.items():
            self.assertEqual(rows[zephyr][1], ubuntu, f"{zephyr} base image")
        dockerfile = (CONTAINER_DIR / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("ARG BASE_IMAGE=", dockerfile)
        self.assertIn("FROM ${BASE_IMAGE}", dockerfile)
        self.assertIn("PIP_BREAK_SYSTEM_PACKAGES=1", dockerfile)
        # Ubuntu 24.04's pip is Debian-packaged with no RECORD file;
        # the upgrade must install over it or the 24.04 builds fail.
        self.assertIn("--ignore-installed --upgrade pip", dockerfile)

    def test_overlay_states_recommended_environment_and_copyright(self):
        overlays = CONTAINER_DIR / "skills" / "version-overlays"
        for zephyr, (cmake, python, ubuntu) in VERSION_MINIMUMS.items():
            body = (overlays / f"{zephyr}.md").read_text(encoding="utf-8")
            self.assertIn("Recommended environment", body, zephyr)
            self.assertIn(f"CMake >= {cmake}", body, zephyr)
            self.assertIn(f"Python >= {python}", body, zephyr)
            self.assertIn(f"ubuntu:{ubuntu}", body, zephyr)
            self.assertIn("Copyright and provenance", body, zephyr)
            self.assertIn("SPDX-License-Identifier: Apache-2.0", body, zephyr)

    def test_full_env_test_script_and_workflow(self):
        # REQ-CONTAINER-009: every version gets a full test — debug
        # and release sysbuilds of a stress sample with MCUboot.
        script = CONTAINER_DIR / "tests" / "full-env-test.sh"
        self.assertTrue(script.is_file())
        body = script.read_text(encoding="utf-8")
        self.assertIn("samples/bluetooth/peripheral", body)
        self.assertIn("SB_CONFIG_BOOTLOADER_MCUBOOT=y", body)
        self.assertIn("CONFIG_DEBUG_OPTIMIZATIONS=y", body)
        self.assertIn("CONFIG_SPEED_OPTIMIZATIONS=y", body)
        self.assertIn("zephyr.signed.bin", body)
        self.assertIn("FULLTEST_ALL_OK", body)
        self.assertIn("SPDX-License-Identifier: Apache-2.0", body)
        dockerfile = (CONTAINER_DIR / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("/opt/west-env/full-env-test.sh", dockerfile)
        workflow = (REPO_ROOT / ".github" / "workflows" / "container-full-test.yml").read_text(encoding="utf-8")
        self.assertIn("zephyrproject-rtos/zephyr", workflow)
        self.assertIn("full-env-test.sh", workflow)
        self.assertIn("west update", workflow)

    def test_publish_workflow_targets_electrohire_ghcr(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "container-images.yml").read_text(encoding="utf-8")
        self.assertIn("ghcr.io/electrohire/zephyr-build-env", workflow)
        self.assertIn("packages: write", workflow)
        self.assertIn("BASE_IMAGE=ubuntu:", workflow)
        self.assertIn("ZEPHYR_SDK_VERSION", workflow)
        self.assertIn("version-overlay.md", workflow)


if __name__ == "__main__":
    unittest.main()
