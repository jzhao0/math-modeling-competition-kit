from __future__ import annotations

import unittest
from pathlib import Path


class PublishWorkflowContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.workflow = (
            self.root / ".github" / "workflows" / "publish-pypi.yml"
        ).read_text(encoding="utf-8")

    def test_manual_dispatch_and_exact_tag_checkout_are_required(self) -> None:
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("ref: refs/tags/${{ inputs.tag }}", self.workflow)
        self.assertIn('python tools/check_release_tag.py "${{ inputs.tag }}"', self.workflow)

    def test_oidc_is_scoped_to_pypi_environment(self) -> None:
        self.assertIn("environment: pypi", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("pypa/gh-action-pypi-publish@release/v1", self.workflow)

    def test_no_long_lived_pypi_secret_contract(self) -> None:
        forbidden = ("PYPI_TOKEN", "TWINE_PASSWORD", "password:", "username: __token__")
        for marker in forbidden:
            self.assertNotIn(marker, self.workflow)

    def test_distribution_audit_precedes_publish_step(self) -> None:
        audit = self.workflow.index("python tools/audit_distribution.py")
        publish = self.workflow.index("pypa/gh-action-pypi-publish@release/v1")
        self.assertLess(audit, publish)

    def test_audit_report_stays_outside_dist_directory(self) -> None:
        self.assertIn("python tools/audit_distribution.py dist --json audit.json", self.workflow)
        self.assertNotIn("--json dist/", self.workflow)


if __name__ == "__main__":
    unittest.main()
