import os
import sys
import logging
from typing import Optional
import dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
dotenv_path = dotenv.find_dotenv()
if dotenv_path:
    logger.info(f"Loading environment variables from {dotenv_path}")
    dotenv.load_dotenv(dotenv_path)
else:
    logger.info("No .env file found, using system environment variables")


def get(name: str, default: Optional[str] = None) -> str:
    """
    Get an environment variable with proper error handling.
    
    Args:
        name: The name of the environment variable to get
        default: An optional default value to return if the variable is not set
        
    Returns:
        The value of the environment variable or the default value
    """
    val = os.getenv(name)
    if val is None:
        if default is not None:
            logger.info(f"Environment variable {name} not set, using default value")
            return default
        logger.error(f"Required environment variable {name} is not set")
        sys.exit(2)
    return val
