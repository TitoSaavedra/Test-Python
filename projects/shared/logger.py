import logging
import logging.handlers
from pathlib import Path


def setup_logger(name: str, log_file: str = None, also_local: bool = True) -> logging.Logger:
    """
    Setup a logger that writes to both console and rotating file handler.
    
    Logs are stored in:
    - Repository root's 'logs' directory (always)
    - Project's local 'logs' directory (if also_local=True)
    
    Args:
        name: Logger name (typically project name)
        log_file: Log file name (defaults to {name}.log)
        also_local: Also save logs to project's local logs directory (default True)
    
    Returns:
        Configured logger instance
    """
    if log_file is None:
        log_file = f"{name}.log"

    root_dir = Path(__file__).parent.parent.parent
    root_log_dir = root_dir / "logs"
    root_log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        root_log_dir / log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Only log to root repo logs directory (no local project logs)

    return logger
