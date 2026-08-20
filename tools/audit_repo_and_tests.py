# -*- coding: utf-8 -*-
import subprocess
import sys

def run_cmd(cmd, description):
    print(f"\n=== {description} ===")
    print(f"$ {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(f"[STDERR]:\n{res.stderr.strip()}")
    return res.returncode

# 1. Check Git Status
run_cmd("git status -s", "1. GIT STATUS (MODIFIED / UNTRACKED FILES)")

# 2. Check Git Remotes & Branch Divergence
run_cmd("git remote -v", "2. CONFIGURED GIT REMOTES")
run_cmd("git branch -vv", "3. CURRENT BRANCH & TRACKING STATUS")

# 3. Run Pytest Suite to check for regressions
print("\n=== 4. RUNNING TEST SUITE (PYTEST) ===")
test_code = run_cmd("pytest -q", "PYTEST REGRESSION SUITE")
if test_code == 0:
    print("\n>>> ALL TESTS PASSED: NO REGRESSIONS DETECTED <<<")
else:
    print(f"\n[WARNING] Tests exited with code {test_code}")