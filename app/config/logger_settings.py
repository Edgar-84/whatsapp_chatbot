import os
import logging
from datetime import datetime

from app.config.project_config import project_settings


class DailyFileHandler(logging.FileHandler):
    def __init__(self, dir_path, filename_prefix, mode='a', encoding=None, delay=False):
        self.dir_path = dir_path
        self.filename_prefix = filename_prefix
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        self.date = datetime.now().strftime('%Y-%m-%d')
        filename = self._get_filename()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        super().__init__(filename, mode, encoding, delay)

    def _get_filename(self):
        return os.path.join(self.dir_path, f"{self.filename_prefix}_{self.date}.log")

    def emit(self, record):
        new_date = datetime.now().strftime('%Y-%m-%d')
        if new_date != self.date:
            self.date = new_date
            self.baseFilename = self._get_filename()
            self.stream.close()
            self.stream = self._open()
        super().emit(record)


def get_logger(name: str = "whatsapp_chatbot") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = DailyFileHandler(project_settings.log_dir, 'log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger
