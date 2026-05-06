from PyQt6 import QtWidgets, QtSvgWidgets, QtCore
from typing import Optional
from discogsrenamer.core.constants import APP_NAME, APP_VERSION, COMPANY_NAME
from discogsrenamer.gui.utils import resource_path


class AboutMessageBox(QtWidgets.QMessageBox):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self) -> None:

        self.setWindowTitle(f"About {APP_NAME}")
        self.setIcon(QtWidgets.QMessageBox.Icon.Information)

        text_label = QtWidgets.QLabel()
        text_label.setWordWrap(True)
        text_label.setFixedWidth(500)
        text_label.setText(
            f"<b><font size=6>{APP_NAME}</font></b><br>"
            f"<br><b><i>{COMPANY_NAME}</i>"
            f"<br>Version {APP_VERSION}<br></b>"
            "<br>I welcome your feedback.  If you have any suggestions, notice a mistake, or experience any technical problems, please get in touch via this project's GitHub page"
            "<br><a href='https://github.com/JimboMonkey/DiscogsRenamer'>https://github.com/JimboMonkey/DiscogsRenamer</a><br>"
            f"<br>Copyright \u00a9 2025-2026 {COMPANY_NAME}<br>"
            "<br>Button icons courtesy of <a href='https://uxwing.com'>UXWing</a><br>"
            "<br>Licensed under the GNU General Public License, version 3 (GPLv3). "
            "You are free to use, modify, and redistribute this software "
            "under the terms of the GPLv3. "
            "This program is distributed WITHOUT ANY WARRANTY; "
            "without even the implied warranty of MERCHANTABILITY "
            "or FITNESS FOR A PARTICULAR PURPOSE<br>"
            "<br>For full license details, visit: "
            "<a href='https://www.gnu.org/licenses/gpl-3.0.html'>https://www.gnu.org/licenses/gpl-3.0.html</a><br>"
        )

        gplv3_logo = QtSvgWidgets.QSvgWidget(
            resource_path("discogsrenamer/gui/icons/gplv3_logo.svg")
        )
        gplv3_logo.setFixedSize(QtCore.QSize(180, 88))

        contents_container = QtWidgets.QWidget()
        vertical_layout = QtWidgets.QVBoxLayout(contents_container)
        vertical_layout.addWidget(
            text_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        vertical_layout.addWidget(
            gplv3_logo, alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        )

        layout = self.layout()
        layout.addWidget(contents_container, 0, 1)

        self.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)

    def show(self) -> None:
        self.exec()
