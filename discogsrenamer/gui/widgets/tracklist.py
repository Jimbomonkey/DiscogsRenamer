from PyQt6 import QtWidgets, QtCore

from typing import Optional, Sequence
from collections import deque
from pathlib import Path
import re
import os

from discogsrenamer.core.settings_protocol import SettingsProtocol
from discogsrenamer.gui.widgets.list_item_widget import ListItemWidget
from discogsrenamer.gui.widgets.release_list_item import ReleaseListItem
from discogsrenamer.gui.widgets.filename_list_item import FilenameListItem
from discogsrenamer.core.models.track_data import TrackData
from discogsrenamer.gui.utils import format_filename, extract_file_extension
from discogsrenamer.core.filename_rules import MAX_FILENAME_LENGTH


class Tracklist(QtWidgets.QListWidget):

    tick_count = QtCore.pyqtSignal(int)
    all_ticked_new_filenames_filled = QtCore.pyqtSignal(bool)

    def __init__(
        self,
        editable: bool,
        settings: SettingsProtocol | None = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        self._editable = editable
        self._settings = settings
        self.parent_widget = parent
        super().__init__(parent)

        # Only folder list items should be selectable and draggable
        if self._editable:
            self.setDragDropMode(QtWidgets.QListWidget.DragDropMode.InternalMove)
            initial_label_text = "Select a folder of audio files"
        else:
            self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            initial_label_text = "Specify a Discogs release number"

        # Label to display list state messages
        self._tracklist_label = QtWidgets.QLabel(initial_label_text)
        self._tracklist_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._tracklist_label.setStyleSheet("color: #888;")
        self._tracklist_label.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        # Set parent to viewport so it sits inside the scroll area
        self._tracklist_label.setParent(self.viewport())
        self.viewport().installEventFilter(self)

        self.model().rowsMoved.connect(self._number_and_shade)
        # Set label visibility when list content changes
        self.model().rowsInserted.connect(self.set_label_visibility)
        self.model().rowsRemoved.connect(self.set_label_visibility)
        self.model().modelReset.connect(self.set_label_visibility)

    # Keep label sized correctly
    def eventFilter(
        self, object: QtCore.QObject | None, event: QtCore.QEvent | None
    ) -> bool:
        if object is self.viewport() and event.type() == QtCore.QEvent.Type.Resize:
            self._tracklist_label.resize(self.viewport().size())

            # Scale font based on height
            font = self._tracklist_label.font()
            font.setPixelSize(max(10, self._tracklist_label.height() // 25))
            self._tracklist_label.setFont(font)

            # Event wasn't consumed
            return False

        return super().eventFilter(object, event)

    # Set label visibility when list content changes
    def set_label_visibility(self) -> None:
        self._tracklist_label.setVisible(self.count() == 0)

    def populate(self, item_list: Sequence[QtWidgets.QListWidgetItem]) -> None:
        # Clear any existing items from the list
        self.clear()

        if not item_list:
            if self._editable:
                self._tracklist_label.setText("Selected folder contains no audio files")
            else:
                self._tracklist_label.setText(
                    "Failed to fetch release\n This release may have been deleted from Discogs"
                )

        matched_track_position = True
        contains_sub_tracks = False

        # For each track name in the list...
        for track_position, item in enumerate(item_list, start=1):

            # Create and configure the custom widget
            widget = item.create_widget()

            self.addItem(item)
            self.setItemWidget(item, widget)
            widget._new_filename.setVisible(self._editable)
            widget._checkbox.stateChanged.connect(self.count_ticks)
            widget._checkbox.stateChanged.connect(
                self.check_all_ticked_new_filenames_filled
            )
            widget._new_filename.textChanged.connect(
                self.check_all_ticked_new_filenames_filled
            )

            if isinstance(item, ReleaseListItem):
                if item.track_data.release.sub_tracks:
                    contains_sub_tracks = True

            if isinstance(item, FilenameListItem):
                if not self.contains_track_position(
                    track_position, item.original_filename
                ):
                    matched_track_position = False

        # Update the track numbers and shading
        self._number_and_shade()
        self.count_ticks()
        if (
            self._settings.get("highlight_track_misnumbering")
            and not matched_track_position
        ):
            QtWidgets.QMessageBox.warning(
                self.parent_widget,
                "Check track order",
                f"The order of the files doesn't match their track positions\n\n"
                "This usually happens when track numbers in filenames aren't zero-padded, causing entries like track 10 to appear immediately after track 1.\n\n"
                "You may need to reorder the list manually by dragging and dropping the tracks. Any mismatched items have been highlighted in red.",
            )

        if contains_sub_tracks:
            messagebox = QtWidgets.QMessageBox(self.parent_widget)
            messagebox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            messagebox.setWindowTitle("Release contains subtracks")
            messagebox.setTextFormat(QtCore.Qt.TextFormat.RichText)
            messagebox.setText(
                "This release contains subtracks. Discogs does not yet provide full subtrack data through their API, "
                "so some track names may not be loaded by this application.<br><br>"
                "If you would like to see subtrack support added, please consider raising a support request with Discogs "
                "so they know that it is important to you.<br><br>"
                "You can submit a “Feature requests / suggestions” ticket here:<br><br>"
                "<a href='https://support.discogs.com/hc/en-us/requests/new'>https://support.discogs.com/hc/en-us/requests/new</a>"
            )

            # Enable clickable links
            messagebox.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextBrowserInteraction
            )
            messagebox.exec()

    def contains_track_position(self, track_position: int, text: str) -> bool:
        # Don't include file extension as it may contain numbers (eg mp3)
        file_name, _ = os.path.splitext(text)
        # Match track position allowing any number of leading zeroes,
        # but only when it is not part of a larger number
        regex_pattern = rf"(?<!\d)0*{track_position}(?!\d)"
        return bool(re.search(regex_pattern, file_name))

    def set_tracklist_label(self, label_text: str) -> None:
        self._tracklist_label.setText(label_text)

    def _number_and_shade(self) -> None:
        number_of_tracks = self.count()
        if self._settings.get("zero_fill_enabled"):
            zfill_width = max(2, len(str(number_of_tracks)))
        else:
            zfill_width = 0

        for index in range(number_of_tracks):
            list_item = self.item(index)
            tracklist_item = self.itemWidget(list_item)
            if isinstance(list_item, FilenameListItem):
                tracklist_item.set_track_number(str(index + 1).zfill(zfill_width))
                if self._settings.get("highlight_track_misnumbering"):
                    matched_state = self.contains_track_position(
                        index + 1, list_item.original_filename
                    )
                    tracklist_item.set_matched_text_colour(matched_state)
            if index % 2 == 1:
                shaded = True
            else:
                shaded = False
            tracklist_item.set_shaded(shaded)

    def list_ticked_tracks(self) -> deque[TrackData]:

        ticked_tracks: deque[TrackData] = deque()

        for index in range(self.count()):
            tracklist_item = self.itemWidget(self.item(index))
            if isinstance(tracklist_item, ListItemWidget):
                if tracklist_item.is_ticked():
                    ticked_tracks.append(self.item(index).track_data)

        return ticked_tracks

    def list_track_renaming_info(self) -> list[tuple[str, Path, Path]]:
        ticked_tracks: list[tuple[str, Path, Path]] = []

        for index in range(self.count()):
            tracklist_item = self.itemWidget(self.item(index))
            if isinstance(tracklist_item, ListItemWidget):
                if tracklist_item.is_ticked():
                    ticked_tracks.append(
                        (
                            tracklist_item.get_track_number(),
                            Path(tracklist_item.get_original_filename()),
                            Path(tracklist_item.get_new_filename()),
                        )
                    )
        return ticked_tracks

    def apply_track_names(
        self, release_tracklist: deque[TrackData] | None, format_str: str
    ) -> None:
        for index in range(self.count()):
            tracklist_item = self.itemWidget(self.item(index))
            if isinstance(tracklist_item, ListItemWidget):
                if not release_tracklist:
                    break
                # Clear the lineedit first
                tracklist_item.set_new_filename("")
                if tracklist_item.is_ticked():
                    new_filename = format_filename(
                        format_str,
                        release_tracklist.popleft(),
                        tracklist_item.get_track_number(),
                    )
                    file_extension = extract_file_extension(
                        tracklist_item.get_original_filename()
                    )
                    full_new_path = new_filename + file_extension
                    if len(full_new_path) > MAX_FILENAME_LENGTH:
                        allowed_base_length = MAX_FILENAME_LENGTH - len(file_extension)
                        truncated_base = new_filename[:allowed_base_length]
                        full_new_path = truncated_base + file_extension
                        QtWidgets.QMessageBox.warning(
                            self.parent_widget,
                            "Filename too long",
                            f"The filename for track {index+1} is longer than the \
                                {MAX_FILENAME_LENGTH} character limit so has been truncated",
                        )
                    tracklist_item.set_new_filename(full_new_path)

    def count_ticks(self) -> None:
        tick_count = 0
        for index in range(self.count()):
            tracklist_item = self.itemWidget(self.item(index))
            if isinstance(tracklist_item, ListItemWidget):
                if tracklist_item.is_ticked():
                    tick_count = tick_count + 1
        self.tick_count.emit(tick_count)

    def check_all_ticked_new_filenames_filled(self) -> None:
        tracklist_items = [
            self.itemWidget(self.item(index)) for index in range(self.count())
        ]

        all_ticked_new_filenames_filled = any(
            tracklist_item.is_ticked() for tracklist_item in tracklist_items
        ) and all(
            tracklist_item.new_filename_filled()
            for tracklist_item in tracklist_items
            if tracklist_item.is_ticked()
        )

        self.all_ticked_new_filenames_filled.emit(all_ticked_new_filenames_filled)
