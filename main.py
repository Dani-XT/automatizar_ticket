from pathlib import Path

from src.app import App

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "src/assets/"


def main():
    app = App(base_dir=BASE_DIR, assets_dir=ASSETS_DIR)
    app.run()

if __name__ == "__main__":
    main()