import os


def _checkdir(folder):
    check = os.path.exists(folder)
    if not(check):
        os.system(f"mkdir -p {folder}")