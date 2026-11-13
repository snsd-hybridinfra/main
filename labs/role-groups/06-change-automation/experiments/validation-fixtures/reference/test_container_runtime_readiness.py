from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import validate_container_runtime_readiness as validator


ROOT = Path(__file__).resolve().parents[1]


class ContainerRuntimeReadinessTests(unittest.TestCase):
    def test_current_blocked_readiness_is_valid(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_unsupported_runtime_promotion_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for relative in (validator.READINESS, validator.RUNNER):
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            path = target / validator.READINESS
            value = json.loads(path.read_text(encoding="utf-8"))
            value["status"] = "READY"
            value["runtime_claim"] = "VALIDATED"
            value["status_credit"]["registry_publish"] = True
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            findings = validator.validate(target)
            self.assertTrue(any("promoted" in item for item in findings))
            self.assertTrue(any("status credit" in item for item in findings))

    def test_unpinned_buildx_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for relative in (validator.READINESS, validator.RUNNER):
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            path = target / validator.RUNNER
            value = json.loads(path.read_text(encoding="utf-8"))
            value["toolchain"] = [
                item for item in value["toolchain"] if item["name"] != "docker-buildx"
            ]
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            findings = validator.validate(target)
            self.assertTrue(any("tool set" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
