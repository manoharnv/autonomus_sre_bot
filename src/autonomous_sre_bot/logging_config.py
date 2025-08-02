"""
Logging configuration for the Autonomous SRE Bot
Disables verbose logging from third-party libraries
"""

import logging
import os


def setup_logging(log_level: str = "INFO"):
    """
    Setup logging configuration with appropriate levels
    
    Args:
        log_level: Root log level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set root logger level
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/autonomous_sre.log'),
            logging.StreamHandler()
        ]
    )
    
    # Disable verbose logging from third-party libraries
    # These libraries are too verbose at DEBUG level
    third_party_loggers = [
        'httpx',
        'httpcore',
        'openai',
        'openai._base_client',  
        'httpcore.http11',
        'urllib3',
        'requests',
        'requests.packages.urllib3',
        'mcp',
        'crewai',
        'litellm'
    ]
    
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)  # Only show warnings and errors
        
    # Keep our own loggers at the specified level
    our_loggers = [
        'autonomous_sre_bot',
        '__main__'
    ]
    
    for logger_name in our_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
    
    # Special case: Set CrewAI to INFO level to see important messages
    logging.getLogger('crewai').setLevel(logging.INFO)
    
    logging.info(f"Logging configured with level: {log_level}")
