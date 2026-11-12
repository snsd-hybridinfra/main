"""Regression and negative tests for the approved composite catalog."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_composite_service_catalog as composite  # noqa: E402


def copied_root() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    for relative in composite.REQUIRED_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return temporary, root


class CompositeServiceCatalogTests(unittest.TestCase):
    def test_current_catalog_is_valid(self) -> None:
        result = composite.validate(ROOT)
        self.assertFalse(result.failures, result.failures)

    def test_free_form_composition_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / composite.CATALOG
            data = json.loads(path.read_text(encoding="utf-8"))
            data["construction_policy"]["free_form_composition"] = True
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = composite.validate(root)
            self.assertTrue(any("free_form_composition" in item for item in result.failures))
        finally:
            temporary.cleanup()

    def test_missing_mandatory_control_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / composite.CATALOG
            data = json.loads(path.read_text(encoding="utf-8"))
            data["blueprints"][0]["components"].remove("NETWORK_POLICY")
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = composite.validate(root)
            self.assertTrue(any("includes network and operations" in item for item in result.failures))
        finally:
            temporary.cleanup()

    def test_production_environment_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / composite.CATALOG
            data = json.loads(path.read_text(encoding="utf-8"))
            data["blueprints"][0]["allowed_environments"].append("PROD")
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = composite.validate(root)
            self.assertTrue(any("non-production" in item for item in result.failures))
        finally:
            temporary.cleanup()

    def test_multicast_leak_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / composite.CATALOG
            data = json.loads(path.read_text(encoding="utf-8"))
            data["blueprints"][0]["network_profile"] = "PRIVATE_MULTICAST"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = composite.validate(root)
            self.assertTrue(any("inherits multicast" in item for item in result.failures))
        finally:
            temporary.cleanup()

    def test_securities_profile_removal_is_rejected(self) -> None:
        temporary, root = copied_root()
        try:
            path = root / composite.CATALOG
            data = json.loads(path.read_text(encoding="utf-8"))
            api = next(
                item for item in data["blueprints"]
                if item["blueprint_id"] == "API_DEVELOPMENT_STACK"
            )
            api["business_domain_profiles"] = []
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            result = composite.validate(root)
            self.assertTrue(any("securities business-domain" in item for item in result.failures))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
