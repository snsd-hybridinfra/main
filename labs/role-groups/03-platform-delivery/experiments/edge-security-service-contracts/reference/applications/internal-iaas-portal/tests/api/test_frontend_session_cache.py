import shutil
import subprocess
from pathlib import Path

import pytest


def test_ecl2_frontend_drops_cross_session_data():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for frontend JavaScript regression")
    script = Path(__file__).parents[1] / "frontend/idp_session_cache.cjs"
    result = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
