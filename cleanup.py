import os
import time

FOLDER = "static/outputs"
MAX_AGE = 24 * 60 * 60  

now = time.time()

for filename in os.listdir(FOLDER):
    filepath = os.path.join(FOLDER, filename)
    if os.path.isfile(filepath):
        file_age = now - os.path.getmtime(filepath)
        if file_age > MAX_AGE:
            os.remove(filepath)
            print(f"Đã xóa: {filename}")
