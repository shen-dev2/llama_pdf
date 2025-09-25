import logging

def setup_logger(log_file: str) -> logging.Logger:
    logger = logging.getLogger("FolderScanner")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger