from PyQt6 import QtWidgets
from pathlib import Path
from pytestqt.qtbot import QtBot
from pytest import MonkeyPatch, fixture, mark
from unittest.mock import patch

from discogsrenamer.core.main_manager import MainManager
from discogsrenamer.core.models.release_data import ReleaseData
from discogsrenamer.core.models.track_data import TrackData

from collections import deque


@fixture
def main_manager_with_folder_path(qtbot: QtBot, tmp_path: Path) -> MainManager:
    main_manager = MainManager()
    main_manager._ui.set_folder_path_label(str(tmp_path))
    return main_manager


@fixture
def file_renaming_info() -> list[tuple[str, Path, Path]]:
    return [
        ("1", Path("1 - firsttrack.mp3"), Path("1 - First.mp3")),
        ("2", Path("2 - secondtrack.mp3"), Path("2 - Second.mp3")),
        ("3", Path("3 - thirdtrack.mp3"), Path("3 - Third.mp3")),
    ]


def test_list_audio_files_in_folder(qtbot: QtBot, tmp_path: Path) -> None:
    main_manager = MainManager()

    test_filenames = ["track_1.mp3", "track_2.MP3", "README", "text_file.txt"]

    for filename in test_filenames:
        (tmp_path / filename).touch()

    audio_file_list = main_manager._list_audio_files_in_folder(tmp_path)

    assert [item.original_filename for item in audio_file_list] == [
        "track_1.mp3",
        "track_2.MP3",
    ]


def test_rename_files(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    main_manager_with_folder_path: MainManager,
    file_renaming_info: list[tuple[str, Path, Path]],
) -> None:

    # Create dummy QMessageBox which simulates an OK click
    def dummy_qmessagebox(
        *args: object, **kwargs: object
    ) -> QtWidgets.QMessageBox.StandardButton:
        return QtWidgets.QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QtWidgets.QMessageBox, "information", dummy_qmessagebox)

    # Create dummy files in tmp_path
    for pair in file_renaming_info:
        (tmp_path / pair[1]).write_text("dummy content")

    main_manager_with_folder_path._rename_files(file_renaming_info)

    # Check files with new names exist
    # and files with old names no longer exist
    for info in file_renaming_info:
        assert (tmp_path / info[2]).exists()
        assert not (tmp_path / info[1]).exists()


@mark.parametrize(
    "exception_type, expected_snippet",
    [
        (FileNotFoundError, "not be found"),
        (PermissionError, "permission denied"),
        (FileExistsError, "already exists"),
    ],
    ids=[
        "File not found",
        "Permission error",
        "File already exists",
    ],
)
@patch("discogsrenamer.core.main_manager.QtWidgets.QMessageBox.critical")
def test_all_rename_errors(
    mock_critical_messagebox: QtWidgets.QMessageBox,
    qtbot: QtBot,
    tmp_path: Path,
    main_manager_with_folder_path: MainManager,
    file_renaming_info: list[tuple[str, Path, Path]],
    exception_type: type[OSError],
    expected_snippet: str,
):
    with patch("os.rename", side_effect=exception_type):

        # Create dummy files in tmp_path
        for pair in file_renaming_info:
            (tmp_path / pair[1]).write_text("dummy content")

        main_manager_with_folder_path._rename_files(file_renaming_info)

        # Check critical messagebox was called and
        # it contains the expected snippet of text
        assert mock_critical_messagebox.called
        args, _ = mock_critical_messagebox.call_args
        assert expected_snippet in args[2].lower()


@fixture
def release_data() -> ReleaseData:
    return ReleaseData(
        release_artists='A Tribe Called Test<>:"/\\|?*',
        release_title='Testify<>:"/\\|?*',
        sub_tracks=False,
    )


def test_sanitise_trackdata(qtbot: QtBot, release_data: ReleaseData) -> None:
    main_manager = MainManager()

    track_data = deque(
        [
            TrackData(
                release=release_data,
                track_position="1",
                track_artists='<>:"/\\|?*',
                track_title='<>:"/\\|?*',
            )
        ]
    )

    INVALID_CHARS_REPLACEMENTS: list[tuple[str, str]] = [
        ("<", "("),
        (">", ")"),
        (":", ""),
        ('"', ""),
        ("/", ","),
        ("\\", ","),
        ("|", ","),
        ("?", ""),
        ("*", ""),
    ]
    sanitised_track_data: deque[TrackData] = main_manager._sanitise_trackdata(
        track_data, INVALID_CHARS_REPLACEMENTS
    )

    assert isinstance(sanitised_track_data, deque)
    assert all(isinstance(item, TrackData) for item in sanitised_track_data)

    expected = "(),,,"

    sanitised_track = sanitised_track_data.pop()

    assert sanitised_track.release.release_artists == "A Tribe Called Test(),,,"
    assert sanitised_track.release.release_title == "Testify(),,,"
    assert sanitised_track.track_artists == expected
    assert sanitised_track.track_title == expected
