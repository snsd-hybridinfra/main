#!/usr/bin/env python3
"""Reject sensitive patterns in a candidate sanitized RV evidence file."""
import argparse,re
from pathlib import Path
PATTERNS={"PRIVATE_KEY":r"-----BEGIN [^-]*PRIVATE KEY-----","TOKEN":r"(?i)\b(?:token|authorization)\s*[:=]\s*(?!\[REDACTED\])\S+","PASSWORD":r"(?i)\bpassword\s*[:=]\s*(?!\[REDACTED\])\S+","MFA_SEED":r"(?i)\b(?:otpauth|mfa[_ -]?seed)\b","MAC_ADDRESS":r"(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b","UUID_INVENTORY":r"(?i)(?:\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b.*){3}","SENSITIVE_PATH":r"(?i)(?:clouds\.yaml|passwords\.yml|\.ssh[\\/]id_)"}
def findings(text): return [name for name,pattern in PATTERNS.items() if re.search(pattern,text,re.S)]
def main()->int:
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("--input",type=Path,required=True); p.add_argument("--verbose",action="store_true"); a=p.parse_args(); bad=findings(a.input.read_text(encoding="utf-8",errors="replace"));
 if a.verbose:
  for item in bad: print(f"[FAIL] {item}")
 print(f"[{'FAIL' if bad else 'PASS'}] sanitizer verification findings={len(bad)}"); return 1 if bad else 0
if __name__=="__main__": raise SystemExit(main())
