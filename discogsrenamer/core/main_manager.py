from PyQt6 import QtCore, QtWidgets

from discogsrenamer.core.app_settings import AppSettings
from discogsrenamer.gui.main_window import MainWindow
from discogsrenamer.gui.widgets.filename_list_item import FilenameListItem
from discogsrenamer.gui.dialogs.settings_dialog import SettingsDialog
from discogsrenamer.gui.dialogs.about_messagebox import AboutMessageBox
from discogsrenamer.core.discogs_manager import DiscogsManager
from discogsrenamer.core.models.track_data import TrackData
from discogsrenamer.gui.utils import open_folder_dialog

from pathlib import Path
import os
from functools import partial
from collections import deque
from typing import Optional


class MainManager(QtCore.QObject):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(MainManager, self).__init__()
        self._settings = AppSettings()
        # Create the main GUI window
        self._ui = MainWindow(self._settings)
        self._discogs_manager = DiscogsManager()
        self.parent_widget = parent

        # Connect signals and slots
        self._ui.release_lineedit.returnPressed.connect(self._load_release)
        self._ui.load_release_button.pressed.connect(self._load_release)
        self._ui.file_browser_button.pressed.connect(self._show_open_dialog)
        self._ui.transfer_button.pressed.connect(self._transfer_track_names)
        self._ui.release_listwidget.tick_count.connect(
            partial(self._ui.handle_tick_count, release_tracklist=True)
        )
        self._ui.folder_listwidget.tick_count.connect(
            partial(self._ui.handle_tick_count, release_tracklist=False)
        )
        self._ui.folder_listwidget.all_ticked_new_filenames_filled.connect(
            self._ui.apply_button_enabled
        )
        self._ui.apply_button.pressed.connect(self._apply_new_names)

        self._ui.settings_action.triggered.connect(lambda: self.open_settings_dialog())

        self._ui.about_action.triggered.connect(lambda: self.open_about_messagebox())

    def extract_digits(self, release_id_string: str) -> int | None:
        digits_string = "".join(
            character for character in release_id_string if character.isdigit()
        )
        return int(digits_string) if digits_string else None

    # Load the release from Discogs and populate the release list
    def _load_release(self) -> None:
        release_id = self.extract_digits(self._ui.release_lineedit.text())
        release = None
        if release_id:
            release = self._discogs_manager.get_release(release_id)
        if release is not None:
            unformatted_release_artists = self._discogs_manager.get_release_artists(
                release
            )
            formatted_release_artists = self._discogs_manager.format_artists(
                unformatted_release_artists
            )
            title = self._discogs_manager.get_release_title(release)
            tracklist = self._discogs_manager.get_tracklist(release)
            track_data_list = self._discogs_manager.get_track_artists_and_titles(
                release, tracklist
            )
            self._ui.update_release_artist_title_label(formatted_release_artists, title)
            self._ui.release_listwidget.populate(track_data_list)
        else:
            self._ui.release_listwidget.set_tracklist_label(
                f"Failed to fetch release {release_id} \n Check the code is correct"
            )

    # Use the standard open dialog box to get the file path of a folder
    def _show_open_dialog(self) -> None:
        folder_path = open_folder_dialog(self._ui, self._settings.get("initial_folder"))

        # Check for file validity here so that cancelling
        # the open dialog doesn't set a blank path
        if (folder_path) and (Path(folder_path).exists()):
            self._read_folder_contents(Path(folder_path))

    # Set the folder path in the GUI and populate
    # the folder list with the names of its files
    def _read_folder_contents(self, folder_path: Path) -> None:
        self._ui.set_folder_path_label(str(folder_path))
        self._ui.update_folder_name_label(folder_path.name)
        file_list = self._list_audio_files_in_folder(folder_path)
        self._ui.folder_listwidget.populate(file_list)
        self._ui.apply_button_enabled(False)

    # Return a sorted list of audio files in a folder
    def _list_audio_files_in_folder(self, folder_path: Path) -> list[FilenameListItem]:

        audio_file_extensions = [
            ".mp3",
            ".wav",
            ".flac",
            ".m4a",
            ".ogg",
            ".aiff",
            ".alac",
            ".wma",
            ".aac",
        ]
        return [
            FilenameListItem(audio_file.name)
            for audio_file in sorted(folder_path.iterdir())
            if audio_file.is_file()
            and audio_file.suffix.lower() in audio_file_extensions
        ]

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self._settings)
        dialog.show()

    def open_about_messagebox(self) -> None:
        _messagebox = AboutMessageBox()

    def _transfer_track_names(self) -> None:
        format_str = self._settings.get("filename_format")
        char_replacements = self._settings.get("invalid_char_replacements")

        ticked_track_list = self._ui.release_listwidget.list_ticked_tracks()

        sanitised_ticked_track_list = self._sanitise_trackdata(
            ticked_track_list, char_replacements
        )

        self._ui.folder_listwidget.apply_track_names(
            sanitised_ticked_track_list, format_str
        )

    def _sanitise_trackdata(
        self,
        track_data: deque[TrackData],
        INVALID_CHARS_REPLACEMENTS: list[tuple[str, str]],
    ) -> deque[TrackData]:

        sanitised_track_data: deque[TrackData] = deque()

        sanitised_table = str.maketrans(dict(INVALID_CHARS_REPLACEMENTS))

        for track in track_data:
            sanitised_track_artists = track.track_artists.translate(sanitised_table)
            sanitised_track_title = track.track_title.translate(sanitised_table)
            sanitised_release_artists = track.release.release_artists.translate(
                sanitised_table
            )
            sanitised_release_title = track.release.release_title.translate(
                sanitised_table
            )
            track.release.release_artists = sanitised_release_artists
            track.release.release_title = sanitised_release_title

            sanitised_track = TrackData(
                release=track.release,
                track_position=track.track_position,
                track_artists=sanitised_track_artists,
                track_title=sanitised_track_title,
            )

            sanitised_track_data.append(sanitised_track)
        return sanitised_track_data

    def _apply_new_names(self) -> None:
        list_of_track_renaming_info = (
            self._ui.folder_listwidget.list_track_renaming_info()
        )
        if list_of_track_renaming_info:
            self._rename_files(list_of_track_renaming_info)

    def _rename_files(
        self, list_of_file_renaming_info: list[tuple[str, Path, Path]]
    ) -> None:

        folder_path: Path | None = self._ui.get_folder_path()

        if folder_path:
            for file_info in list_of_file_renaming_info:
                original_filename = file_info[1]
                new_filename = file_info[2]
                full_original_file_path = folder_path / original_filename
                _, file_extension = os.path.splitext(full_original_file_path)
                full_prefix = Path(str(new_filename))

                full_new_file_path = folder_path / full_prefix.with_suffix(
                    file_extension
                )
                os.rename(
                    full_original_file_path,
                    full_new_file_path.with_suffix(file_extension),
                )
            QtWidgets.QMessageBox.information(
                self.parent_widget,
                "Rename Complete",
                f"Files of {folder_path} renamed successfully",
            )
            self._read_folder_contents(folder_path)
