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


def _matrix_pairs():
    """Parse the Zephyr -> SDK matrix out of build-matrix.sh."""
    text = (CONTAINER_DIR / "build-matrix.sh").read_text(encoding="utf-8")
    return re.findall(r"^(\d+\.\d+\.\d+) (\d+\.\d+\.\d+)$", text, re.M)


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

    def test_publish_workflow_targets_electrohire_ghcr(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "container-images.yml").read_text(encoding="utf-8")
        self.assertIn("ghcr.io/electrohire/zephyr-build-env", workflow)
        self.assertIn("packages: write", workflow)
        self.assertIn("ZEPHYR_SDK_VERSION", workflow)
        self.assertIn("version-overlay.md", workflow)


if __name__ == "__main__":
    unittest.main()
