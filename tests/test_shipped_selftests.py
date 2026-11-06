"""Run the self-test that ships inside the package.

src/szl_substrate/test_szl_hf_bucket.py is the byte-extracted unit test of
szl_hf_bucket. It lives in the package (not under tests/), imports
``szl_hf_bucket`` as a bare name and is meant to be run by file path, so the
configured testpaths never collected it. Running it in a subprocess executes
it exactly as documented without putting the package directory on this
process's sys.path.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import szl_substrate


def test_szl_hf_bucket_self_test_passes():
    script = Path(szl_substrate.__file__).resolve().parent / "test_szl_hf_bucket.py"
    assert script.is_file()
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                          timeout=300, check=False)
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-4000:]
    assert "\nOK" in proc.stderr and " 0 tests" not in proc.stderr
