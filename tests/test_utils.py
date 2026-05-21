from discogsrenamer.gui.utils import extract_file_extension
from discogsrenamer.gui.utils import format_filename
from discogsrenamer.core.app_settings import DEFAULT_SETTINGS
from discogsrenamer.core.models.track_data import TrackData

import pytest
from unittest.mock import MagicMock


@pytest.mark.parametrize(
    "test_path, expected_response",
    [
        ("/test/dir/test_track.mp3", ".mp3"),
        ("/test/dir/test_track.MP3", ".mp3"),
        ("/test/dir/test_README", ""),
    ],
)
def test_extract_file_extension(test_path: str, expected_response: str) -> None:
    file_extension = extract_file_extension(test_path)
    assert file_extension == expected_response


def test_format_filename() -> None:
    format_str: str = DEFAULT_SETTINGS.get("filename_format")
    track_num = "1"

    test_track_artists = "Sir Test-a-lot"
    test_track_title = "Test Side Story"

    track_data = TrackData(
        release=MagicMock(),
        # The TrackData track position is not
        # used by format_filename. It uses the
        # passed in track_num instead
        track_position="2",
        track_artists=test_track_artists,
        track_title=test_track_title,
    )

    new_filename = format_filename(
        format_str,
        track_data,
        track_num,
    )

    assert new_filename == f"{track_num} - {test_track_artists} - {test_track_title}"
