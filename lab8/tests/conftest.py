import os
import pytest
import yaml
import requests

SPEC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openapi.yaml")
PRISM_BASE = "http://localhost:4010"


@pytest.fixture(scope="session")
def spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _prism_running() -> bool:
    try:
        requests.get(f"{PRISM_BASE}/", timeout=1)
        return True
    except Exception:
        return False


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "prism: requires Prism mock server (docker compose up)"
    )


def pytest_collection_modifyitems(config, items):
    skip = pytest.mark.skip(reason="Prism not running — start with: docker compose up -d")
    for item in items:
        if "prism" in item.keywords and not _prism_running():
            item.add_marker(skip)
