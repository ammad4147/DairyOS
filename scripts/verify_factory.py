"""
PowerShelf‑ready test script – run it from PowerShell:

    python dairyos/scripts/verify_factory.py

It will print the fully‑qualified Python types that the
DashboardFactory creates.
"""

import os
import sys

# Make sure the repo root (the parent of the `scripts` dir) is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Now we can import the real code
from dairyos.application.application_runtime import ApplicationRuntime
from dairyos.application.dashboard.dashboard_factory import DashboardFactory


def main() -> None:
    # 1. Instantiate the runtime (this pulls in all infrastructure objects)
    runtime = ApplicationRuntime()

    # 2. Create the factory with that runtime
    factory = DashboardFactory(runtime)

    # 3. Print the type information
    print("StateQueryService   :", type(factory.state_query_service).__module__)
    print("BuilderService      :", type(factory.builder_service).__module__)
    print("SummaryService      :", type(factory.summary_service).__module__)


if __name__ == "__main__":
    main()
