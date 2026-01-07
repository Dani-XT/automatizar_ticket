from pathlib import Path

from src.app import App

BASE_DIR = Path(__file__).resolve().parent

def main():
    app = App(base_dir=BASE_DIR)
    app.run()

if __name__ == "__main__":
    main()