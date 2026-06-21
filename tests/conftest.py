import sys
from pathlib import Path
import pytest

# Ensure project root is on path when running pytest
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture
def project_root() -> Path:
    return ROOT
