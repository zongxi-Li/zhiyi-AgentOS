from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
AGENT_ROOT = APP_ROOT.parent
PROJECT_ROOT = AGENT_ROOT.parent

APP_DATA_DIR = APP_ROOT / "data"
RAG_DATA_DIR = APP_DATA_DIR / "rag"
DIGITAL_HUMAN_DATA_DIR = APP_DATA_DIR / "digital-human"
DIGITAL_HUMAN_IMAGE_DIR = DIGITAL_HUMAN_DATA_DIR / "images" / "realistic"
DIGITAL_HUMAN_METADATA_DIR = DIGITAL_HUMAN_DATA_DIR / "metadata"
