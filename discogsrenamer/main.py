import sys

from PyQt6.QtWidgets import QApplication

from discogsrenamer.core.main_manager import MainManager


# Start the application
def main() -> None:
    application = QApplication(sys.argv)

    main_manager = MainManager()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
