"""
Logging Configuration

Centralized logging setup for Word Quest.
Import and call setup_logging() at the start of __main__.py.
"""

import logging
import sys


def setup_logging() -> None:
    """
    Configure logging for the application.
    
    Sets up basic configuration with INFO level and formatted output.
    Should be called once at application startup.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )