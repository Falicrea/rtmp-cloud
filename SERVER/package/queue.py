import threading
import time
import os
import shutil
from datetime import datetime

from . import utils, logger

def remove_old_stream():
    folders = [f for f in os.listdir(utils.hls_directory) if os.path.isdir(os.path.join(utils.hls_directory, f))]
    while True:

        # get the current date and time
        now = datetime.now()

        # get the creation date of each folder
        for folder in folders:
            folder_path = os.path.join(utils.hls_directory, folder)
            creation_date = datetime.fromtimestamp(os.path.getctime(folder_path))
            # calculate the age of the folder in hours
            age_hours = (now - creation_date).total_seconds() / 3600
            if age_hours > 72:
                # Remove the folder
                shutil.rmtree(folder_path, ignore_errors=True)
                logger.logger.info(f"Remove stream name: {folder}")

        time.sleep(3600)  # One hour


def run_queue():
    rm = threading.Thread(target=remove_old_stream(), args=())
    rm.start()