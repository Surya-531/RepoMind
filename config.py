import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("repomind")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "anthropic/claude-3-haiku"

# Limits
README_CHAR_LIMIT = 3000
FILE_LIMIT = 50
COMMIT_LIMIT = 5

# Optional GitHub token (increases rate limit from 60 to 5000 req/hr)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

if not OPENROUTER_API_KEY:
    raise EnvironmentError("OPENROUTER_API_KEY is not set. Please check your .env file.")
