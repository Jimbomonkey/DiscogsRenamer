from discogsrenamer.core.main_manager import MainManager
from discogsrenamer.gui.main_window import MainWindow
from pytestqt.qtbot import QtBot
from collections import deque
from pathlib import Path

from discogsrenamer.core.app_settings import AppSettings
from discogsrenamer.core.settings_protocol import SettingsProtocol
from discogsrenamer.core.models.release_data import ReleaseData
from discogsrenamer.core.models.track_data import TrackData
from discogsrenamer.gui.widgets.filename_list_item import FilenameListItem
from discogsrenamer.gui.widgets.release_list_item import ReleaseListItem

import pytest


@pytest.fixture
def app_settings() -> SettingsProtocol:
    return AppSettings()


@pytest.fixture
def main_window(
    qtbot: QtBot,
    app_settings: SettingsProtocol,
) -> MainWindow:
    window = MainWindow(app_settings)
    qtbot.add_widget(window)
    return window


# Test that the release lineedit accepts valid inputs
@pytest.mark.parametrize(
    "valid_input",
    [
        "12345",  # Only digits
        "r12345",  # r followed by digits
        "[r12345]",  # r followed by bracketed digits
    ],
)
def test_release_lineedit_accepts_valid_inputs(
    qtbot: QtBot, main_window: MainWindow, valid_input: str
) -> None:

    line_edit = main_window.release_lineedit
    validator = line_edit.validator()
    assert validator is not None

    line_edit.setText(valid_input)
    qtbot.waitSignal(line_edit.textChanged)
    assert line_edit.hasAcceptableInput()


# Test that the release lineedit rejects invalid inputs
@pytest.mark.parametrize(
    "invalid_input",
    [
        "abcde",
        "rabcde",
        "[rabcde]",
        "r12345abc",
        "[r12345abc]",
        "[r12345",
        "r12345]",
        "[r12 345]",
        "[r!@#$%]",
        "01234",
        "r01234",
        "[r01234]",
    ],
    ids=[
        "only_letters",
        "r_followed_by_letters",
        "bracketed_r_followed_by_letters",
        "r_followed_by_digits_and_letters",
        "bracketed_r_followed_by_digits_and_letters",
        "r_followed_by_unclosed_bracket",
        "r_followed_by_unstarted_bracket",
        "bracketed_r_followed_by_digits_with_space",
        "bracketed_r_followed_by_special_characters",
        "leading_zero",
        "r_followed_by_leading_zero",
        "bracketed_r_followed_by_leading_zero",
    ],
)
def test_release_lineedit_rejects_invalid_inputs(
    qtbot: QtBot, main_window: MainWindow, invalid_input: str
) -> None:

    line_edit = main_window.release_lineedit
    validator = line_edit.validator()
    assert validator is not None

    line_edit.setText(invalid_input)
    qtbot.waitSignal(line_edit.textChanged)
    assert not line_edit.hasAcceptableInput()


# Ensure load release button is only enabled when valid text is entered
def test_load_release_button_enabled_by_text(main_window: MainWindow) -> None:

    line_edit = main_window.release_lineedit
    button = main_window.load_release_button

    # Initially, the button should be disabled
    assert not button.isEnabled()

    # Simulate valid input
    line_edit.setText("[r12345]")
    assert button.isEnabled()


@pytest.mark.parametrize(
    "release_ticks, folder_ticks, expected_response",
    [
        (5, 5, True),
        (0, 0, False),
        (3, 4, False),
        (0, 2, False),
    ],
    ids=["equal_nonzero", "equal_zero", "unequal", "unequal_one_zero"],
)
def test_compare_counts(
    main_window: MainWindow,
    release_ticks: int,
    folder_ticks: int,
    expected_response: bool,
):

    main_window.ticked_release_tracks = release_ticks
    main_window.ticked_folder_tracks = folder_ticks

    main_window.compare_counts()

    assert main_window.transfer_button.isEnabled() == expected_response


def test_apply_button_enabled(main_window: MainWindow) -> None:

    apply_button = main_window.apply_button

    # Initially, the button should be disabled
    assert not apply_button.isEnabled()

    # Simulate true condition
    main_window.apply_button_enabled(True)
    assert apply_button.isEnabled()

    # Simulate false condition
    main_window.apply_button_enabled(False)
    assert not apply_button.isEnabled()


def test_update_release_artist_title_label(main_window: MainWindow) -> None:

    test_artist = "DJ Test"
    test_title = "Testing The Night Away"

    label = main_window.release_artist_title_label
    main_window.update_release_artist_title_label(test_artist, test_title)
    assert label.text() == f"{test_artist} - {test_title}"


def test_update_folder_name_label(main_window: MainWindow) -> None:

    test_folder_name = "DJ Test - Testing The Night Away"

    label = main_window.folder_name_label
    main_window.update_folder_name_label(test_folder_name)
    assert label.text() == test_folder_name


def test_apply_button_enabled_when_all_filenames_populated(qtbot: QtBot) -> None:
    main_manager = MainManager()
    main_window = main_manager._ui
    qtbot.addWidget(main_window)

    test_tracklist = [
        FilenameListItem("01 - Untitled.mp3"),
        FilenameListItem("02 - Untitled.mp3"),
        FilenameListItem("03 - Untitled.mp3"),
    ]

    release_data = ReleaseData(
        release_artists="DJ Test & The Testers",
        release_title="Testing The Night Away",
        sub_tracks=False,
    )

    ticked_tracks: deque[TrackData] = deque()

    test_new_filenames = [
        ReleaseListItem(
            TrackData(
                release=release_data,
                track_position="1",
                track_artists="Kanye Test",
                track_title="Through The Test",
            )
        ),
        ReleaseListItem(
            TrackData(
                release=release_data,
                track_position="2",
                track_artists="Testlife",
                track_title="I Love To Test",
            )
        ),
        ReleaseListItem(
            TrackData(
                release=release_data,
                track_position="3",
                track_artists="The Chemical Brothers",
                track_title="The Test",
            )
        ),
    ]
    for entry in test_new_filenames:
        ticked_tracks.append(entry.track_data)

    main_window.folder_listwidget.populate(test_tracklist)

    # Initially, the button should be disabled
    assert not main_window.apply_button.isEnabled()

    # Simulate valid input
    main_window.folder_listwidget.apply_track_names(ticked_tracks, "%tt")
    assert main_window.apply_button.isEnabled()


def test_set_folder_path_label(main_window: MainWindow) -> None:

    test_folder_path = "/test/folder/path"

    main_window.set_folder_path_label(test_folder_path)
    assert main_window.folder_entry_label.text() == test_folder_path


def test_get_folder_path(main_window: MainWindow) -> None:

    test_folder_path = "/test/folder/path"

    # First check when the folder path hasn't been set yet
    folder_path = main_window.get_folder_path()
    assert folder_path is None

    # Then check once set
    main_window.set_folder_path_label(test_folder_path)
    folder_path = main_window.get_folder_path()
    assert isinstance(folder_path, Path)
    assert folder_path == Path(test_folder_path)
