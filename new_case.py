import sys,os

args = sys.argv

new_folder = sys.argv[1]

os.system(f"mkdir -p {new_folder}")
os.system(f"cp config.yml {new_folder}/.")
os.system(f"cp main_proc.py {new_folder}/.")
