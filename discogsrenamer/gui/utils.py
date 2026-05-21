from PyQt6 import QtCore, QtGui, QtWidgets
from dataclasses import asdict
import os
import sys
from pathlib import Path
from typing import Any

from discogsrenamer.core.filename_rules import get_invalid_filename_characters
from discogsrenamer.core.models.track_data import TrackData


def open_folder_dialog(parent: QtWidgets.QWidget | None, initial_folder: str) -> str:
    return QtWidgets.QFileDialog.getExistingDirectory(
        parent,
        "Select Folder",
        initial_folder,
        options=(
            QtWidgets.QFileDialog.Option.ShowDirsOnly
            | QtWidgets.QFileDialog.Option.DontUseNativeDialog
        ),
    )


# Flatten TrackData dataclass objects into a dict, including nested release
def track_data_to_dict(track_data: TrackData) -> dict[str, Any]:
    d = asdict(track_data)
    # Merge the nested release's fields into the top-level dict
    if "release" in d and isinstance(d["release"], dict):
        release_fields = d.pop("release")
        d.update(release_fields)
    return d


def format_filename(template: str, track_data: TrackData, track_num: str) -> str:
    flat_dict = track_data_to_dict(track_data)
    flat_dict["track_num"] = track_num
    safe = (
        template.replace("%ra", "{release_artists}")
        .replace("%rt", "{release_title}")
        .replace("%rn", "{track_position}")
        .replace("%ta", "{track_artists}")
        .replace("%tt", "{track_title}")
        .replace("%fn", "{track_num}")
    )
    return safe.format(**flat_dict)


def extract_file_extension(file_path: str) -> str:
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower()


def make_filename_validator() -> QtGui.QRegularExpressionValidator:
    invalid_characters_list = get_invalid_filename_characters()
    invalid_characters = "".join(
        QtCore.QRegularExpression.escape(character)
        for character, _ in invalid_characters_list
    )
    regex = QtCore.QRegularExpression(f"[^{invalid_characters}]*")
    return QtGui.QRegularExpressionValidator(regex)


# Return absolute path to a resource
def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parents[2]
    return str(base / relative_path)
