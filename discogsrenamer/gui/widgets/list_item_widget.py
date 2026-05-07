from PyQt6 import QtWidgets, QtCore
from typing import Optional

from discogsrenamer.gui.utils import make_filename_validator
from discogsrenamer.core.filename_rules import MAX_FILENAME_LENGTH


class ListItemWidget(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)

        # Create the display widgets
        self._original_filename = QtWidgets.QLabel()
        self._new_filename = QtWidgets.QLineEdit()
        self._new_filename.setMaxLength(MAX_FILENAME_LENGTH)
        self._new_filename.setValidator(make_filename_validator())
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setChecked(True)

        self._original_filename.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )

        # Layout the filenames vertically
        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.addWidget(self._original_filename)
        vertical_layout.addWidget(self._new_filename)

        self._track_number = QtWidgets.QLabel()
        self._track_number.setContentsMargins(15, 0, 15, 0)

        self.horizontal_layout = QtWidgets.QHBoxLayout()
        self.horizontal_layout.addWidget(self._track_number)
        self.horizontal_layout.addLayout(vertical_layout)
        self.horizontal_layout.addWidget(self._checkbox)
        self.setLayout(self.horizontal_layout)

    def set_matched_text_colour(self, matched_state: bool):
        if matched_state:
            # Inherit the colour from the parent/system theme
            # (eg dark theme) rather than hardcoding black
            stylesheet = "color: inherit;"
        else:
            stylesheet = "color: red;"
        self._track_number.setStyleSheet(stylesheet)
        self._original_filename.setStyleSheet(stylesheet)

    def set_track_number(self, text: str) -> None:
        self._track_number.setText(text)

    def get_track_number(self) -> str:
        return self._track_number.text()

    def set_shaded(self, shaded: bool) -> None:
        if shaded:
            self.setStyleSheet("background-color: lightgray;")
        else:
            self.setStyleSheet("background-color: none;")

    # Set the upper label with the original filename of the file
    def set_original_filename(self, text: str) -> None:
        self._original_filename.setText(text)

    # Set the lower lineedit with the new filename for the file
    def set_new_filename(self, text: str) -> None:
        self._new_filename.setText(text)

    # Return state of checkbox
    def is_ticked(self) -> bool:
        return self._checkbox.isChecked()

    # Return the original filename of the file
    def get_original_filename(self) -> str:
        return self._original_filename.text()

    # Return the original filename of the file
    def get_new_filename(self) -> str:
        return self._new_filename.text()

    # Return whether new_filename lineedit contains text or not
    def new_filename_filled(self) -> bool:
        return bool(self._new_filename.text().strip())
