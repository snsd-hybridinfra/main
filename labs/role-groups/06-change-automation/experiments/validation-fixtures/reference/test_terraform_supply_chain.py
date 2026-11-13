from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import validate_terraform_supply_chain as validator


ROOT = Path(__file__).resolve().parents[1]


class TerraformSupplyChainRepositoryTests(unittest.TestCase):
    def test_current_authorities_are_valid(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_runtime_status_overclaim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for source in (
                validator.AUTHORITY,
                validator.DECISION,
                validator.LOCK,
                validator.CATALOG,
                validator.EXECUTOR,
                validator.POLICY_MODULE,
                validator.POLICY_TEST,
            ):
                destination = target / source.relative_to(ROOT)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            authority = target / validator.AUTHORITY.relative_to(ROOT)
            value = json.loads(authority.read_text(encoding="utf-8"))
            value["status"]["runtime"] = "RUNTIME_VALIDATED"
            authority.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(any("promoted" in finding for finding in validator.validate(target)))


if __name__ == "__main__":
    unittest.main()
