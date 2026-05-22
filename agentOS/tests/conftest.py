import sys
from pathlib import Path


AGENTOS_ROOT = Path(__file__).resolve().parents[1]
AGENTOS_SRC = AGENTOS_ROOT / "src"

value = str(AGENTOS_SRC)
if value not in sys.path:
    sys.path.insert(0, value)
