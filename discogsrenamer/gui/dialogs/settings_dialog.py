from discogsrenamer.core.settings_protocol import SettingsProtocol
from discogsrenamer.gui.dialogs.settings_dialog_gui import SettingsDialogGui

from discogsrenamer.gui.utils import make_filename_validator
from discogsrenamer.core.app_settings import DEFAULT_SETTINGS


class SettingsDialog:

    def __init__(self, settings: SettingsProtocol) -> None:

        self._settings = settings
        self._ui = SettingsDialogGui()
        self._ui.format_lineedit.setValidator(make_filename_validator())

        self._init_connections()

    def show(self) -> None:
        self._set_gui_values()
        self._ui.exec()  # only run modal loop when explicitly asked

    # Link GUI widgets to the functions
    def _init_connections(self) -> None:
        self._ui.initial_folder_button.clicked.connect(
            self._ui.open_initial_folder_dialog
        )
        self._ui.cancel_button.clicked.connect(self._ui.close_dialog)
        self._ui.restore_defaults_button.clicked.connect(self.restore_defaults)
        self._ui.close_button.clicked.connect(self._ui.close_dialog)
        self._ui.close_button.clicked.connect(self.save_settings)

    def get_invalid_char_replacements(self) -> list[tuple[str, str]]:
        return self._ui.invalid_char_table.model().get_data()

    def save_settings(self) -> None:
        self._settings.set("filename_format", self._ui.format_lineedit.text())
        self._settings.set("zero_fill_enabled", self._ui.zero_fill_checkbox.isChecked())
        self._settings.set(
            "highlight_track_misnumbering",
            self._ui.misnumbering_warning_checkbox.isChecked(),
        )
        self._settings.set(
            "initial_folder",
            self._ui.initial_folder_lineedit.text(),
        )
        self._settings.set(
            "invalid_char_replacements", self.get_invalid_char_replacements()
        )

    def restore_defaults(self) -> None:
        self._ui.format_lineedit.setText(DEFAULT_SETTINGS["filename_format"])
        self._ui.zero_fill_checkbox.setChecked(DEFAULT_SETTINGS["zero_fill_enabled"])
        self._ui.misnumbering_warning_checkbox.setChecked(
            DEFAULT_SETTINGS["highlight_track_misnumbering"]
        )
        self._ui.initial_folder_lineedit.setText(DEFAULT_SETTINGS["initial_folder"])
        self._ui.invalid_char_table.set_data(
            DEFAULT_SETTINGS["invalid_char_replacements"]
        )

    def _set_gui_values(self) -> None:
        self._ui.format_lineedit.setText(self._settings.get("filename_format"))
        self._ui.zero_fill_checkbox.setChecked(self._settings.get("zero_fill_enabled"))
        self._ui.misnumbering_warning_checkbox.setChecked(
            self._settings.get("highlight_track_misnumbering")
        )
        self._ui.initial_folder_lineedit.setText(self._settings.get("initial_folder"))
        self._ui.invalid_char_table.set_data(
            self._settings.get("invalid_char_replacements")
        )
