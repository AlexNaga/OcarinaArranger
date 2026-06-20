"""Compatibility wrapper exposing :class:`ui.main_window.MainWindow` as ``App``."""

from __future__ import annotations

import sys
import tkinter as tk

from ui.main_window import MainWindow


class App(MainWindow):
    """Legacy alias retaining the public ``ocarina_gui.app.App`` entry point."""


def _main() -> None:
    app = App()
    app.start_automatic_update_check()
    _bind_global_keys(app)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if path.endswith(".ocarina"):
            app.after(100, lambda: app._load_project_from_path(path))
        else:
            app.after(100, lambda: _import_source_file(app, path))
    app.mainloop()


def _import_source_file(app: App, path: str) -> None:
    app._viewmodel.update_settings(input_path=path)
    app.input_path.set(path)
    app._sync_controls_from_state()
    app._mark_preview_stale()
    app._select_preview_tab("arranged")
    app._auto_render_preview(app._preview_frame_for_side("arranged"))
    # Set default playback tempo to 60 BPM
    tempo_var = app._preview_tempo_vars.get("arranged")
    if tempo_var is not None:
        tempo_var.set(60)


def _bind_global_keys(app: App) -> None:
    def _toggle_play(event):
        # Allow Space in text entry widgets
        widget = event.widget
        if isinstance(widget, (tk.Entry, tk.Text)):
            return
        # Prevent ttk buttons from also firing
        try:
            widget_class = widget.winfo_class()
        except tk.TclError:
            widget_class = ""
        if widget_class in ("TButton", "Button", "TCheckbutton"):
            return
        playback = app._preview_playback.get("arranged")
        if playback is None or not playback.state.is_loaded:
            return "break"
        if playback.state.is_playing:
            playback.toggle_playback()
        else:
            playback.seek_to(0)
            playback.toggle_playback()
        app._update_playback_visuals("arranged")
        return "break"

    # Bind on the window itself and steal focus to it
    app.bind("<KeyPress-space>", _toggle_play)
    app.bind_all("<space>", _toggle_play)
    app.after(200, lambda: app.focus_set())


if __name__ == "__main__":
    _main()
