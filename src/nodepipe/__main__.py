import sys
from pathlib import Path

# Fix import path for exe
cd = str(Path(__file__).resolve().parent)
if cd not in sys.path:
    sys.path.insert(0, cd)


from app import App

if __name__ == "__main__":
    App.bootup()