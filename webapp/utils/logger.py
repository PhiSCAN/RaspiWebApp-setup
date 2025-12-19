import logging, os
from datetime import datetime

def read_latest_log_lines(log_dir="logs", num_lines=100):
    # Get all .log files
    log_files = [
        os.path.join(log_dir, f)
        for f in os.listdir(log_dir)
        if f.endswith(".log")
    ]

    if not log_files:
        return []

    # Get latest modified log file
    latest_log = max(log_files, key=os.path.getmtime)

    # Read last `num_lines` lines
    with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    return lines[-num_lines:]


class MonthlyFileHandler(logging.Handler):
    def __init__(self, log_dir="logs"):
        super().__init__()
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        self._update_filename()
        self._open_file()

    def _update_filename(self):
        # Monthly log file: "October 2025.log"
        now = datetime.now()
        self.filename = os.path.join(self.log_dir, f"{now.strftime('%B_%Y')}.log")

    def _open_file(self):
        self.stream = open(self.filename, 'a', encoding='utf-8')

    def emit(self, record):
        # Update filename if month changed
        self._update_filename()
        if self.stream.name != self.filename:
            self.stream.close()
            self._open_file()

        msg = self.format(record)
        self.stream.write(msg + "\n")
        self.stream.flush()

    def close(self):
        self.stream.close()
        super().close()


def setup_logger(app_name="flask_app"):
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)  # Minimum level to capture

    # Monthly file handler
    file_handler = MonthlyFileHandler()
    file_handler.setLevel(logging.INFO)  # Logs INFO and above

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
