"""
Shared pytest setup.

The default test run is offline: LLM settings are blanked before any game
module loads .env, so nothing calls Gemini or a vLLM server. Scripts that
need a live LLM or a running API server live in tests/live/ and are only
collected with ``pytest --live`` (most of them are meant to be run directly
with ``python tests/live/<script>.py``).
"""

import os
import sys

# Blank (not delete) so load_dotenv(), which never overrides existing
# variables, can't fill them back in from the developer's .env.
for _var in ("LLM_PROVIDER", "VLLM_BASE_URL", "VLLM_MODEL", "VLLM_API_KEY",
             "GOOGLE_API_KEY", "GEMINI_API_KEY"):
    os.environ[_var] = ""

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def pytest_addoption(parser):
    parser.addoption(
        "--live", action="store_true", default=False,
        help="also collect tests/live (needs a real LLM and/or a running API server)",
    )


def pytest_ignore_collect(collection_path, config):
    if collection_path.name == "live" and not config.getoption("--live"):
        return True
    return None
