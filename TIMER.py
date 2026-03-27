import os
import math
import time
import tkinter as tk
from tkinter import colorchooser, font, messagebox, ttk


# GUI customization section
# Edit these defaults directly if you want to quickly change the look of the app.
DEFAULT_PALETTE = {
    "control_bg": "#16212B",
    "control_fg": "#F5F7FA",
    "panel_bg": "#22313D",
    "panel_border": "#3B5365",
    "entry_bg": "#F4F6F8",
    "entry_fg": "#16212B",
    "display_bg": "#050B10",
    "normal_digits": "#41D66D",
    "warning_digits": "#FFD447",
    "overtime_digits": "#FF4D4D",
    "status_text": "#DDE6ED",
    "start_button_bg": "#2E8B57",
    "stop_button_bg": "#B03A2E",
    "reset_button_bg": "#2C5AA0",
    "utility_button_bg": "#516B7B",
    "button_fg": "#FFFFFF",
}

DEFAULT_FONTS = {
    "control_family": "Segoe UI",
    "control_size": 11,
    "digit_family": "Consolas",
    "digit_scale": 90,
}

DEFAULT_WINDOW = {
    "control_geometry": "540x760+80+80",
    "display_geometry": "980x360+650+120",
    "borderless_display": False,
    "display_always_on_top": True,
}

ICON_CONFIG = {
    "icon_folder": "ICON",
    "window_icon": "WIN.ico",
    "desktop_icon": "DESK.ico",
}


class SpeakerTimerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.palette = DEFAULT_PALETTE.copy()
        self.font_settings = DEFAULT_FONTS.copy()
        self.window_settings = DEFAULT_WINDOW.copy()
        self.icon_config = ICON_CONFIG.copy()

        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.settings_window = None
        self.settings_controls = {}
        self.update_job = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        default_duration = 15 * 60
        default_warning = 2 * 60
        self.speaker_order = ("speaker_1", "speaker_2")
        self.active_speaker_var = tk.StringVar(value="speaker_1")
        self.speaker_data = {}
        for speaker_index, speaker_key in enumerate(self.speaker_order, start=1):
            self.speaker_data[speaker_key] = {
                "label": f"Speaker {speaker_index}",
                "short_label": f"SPKR {speaker_index}",
                "duration_seconds": default_duration,
                "warning_seconds": default_warning,
                "current_remaining_seconds": float(default_duration),
                "timer_running": False,
                "end_monotonic": 0.0,
                "time_var": tk.StringVar(
                    value=self.format_time_for_entry(default_duration)
                ),
                "warning_var": tk.StringVar(
                    value=self.format_time_for_entry(default_warning)
                ),
            }

        self.current_display_var = tk.StringVar(value="15:00")
        self.status_var = tk.StringVar(value="Stopped")
        self.borderless_var = tk.BooleanVar(
            value=self.window_settings["borderless_display"]
        )
        self.always_on_top_var = tk.BooleanVar(
            value=self.window_settings["display_always_on_top"]
        )

        self.frame_widgets = []
        self.panel_frame_widgets = []
        self.label_widgets = []
        self.entry_widgets = []
        self.check_widgets = []
        self.radio_widgets = []
        self.button_styles = []

        self.configure_root()
        self.build_menu()
        self.build_control_panel()
        self.build_display_window()
        self.bind_shortcuts()
        self.apply_theme()
        self.refresh_clock_faces()
        self.root.after_idle(self.apply_display_window_flags)
        self.root.after_idle(self.fit_control_window_to_content)
        self.root.after_idle(self.update_display_font)
        self.update_timer_loop()

    def configure_root(self) -> None:
        self.root.title("Inspired Speaker Timer")
        self.root.geometry(self.window_settings["control_geometry"])
        self.root.minsize(460, 560)
        self.root.configure(bg=self.palette["control_bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)
        self.apply_window_icon(self.root)

    def get_speaker_state(self, speaker_key=None) -> dict:
        return self.speaker_data[speaker_key or self.active_speaker_var.get()]

    def get_icon_path(self, icon_key: str) -> str:
        return os.path.join(
            self.base_dir,
            self.icon_config["icon_folder"],
            self.icon_config[icon_key],
        )

    def apply_window_icon(self, window: tk.Misc) -> None:
        icon_path = self.get_icon_path("window_icon")
        if not os.path.exists(icon_path):
            return
        try:
            window.iconbitmap(icon_path)
        except tk.TclError:
            pass

    def on_control_main_frame_configure(self, _event=None) -> None:
        self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))

    def on_control_canvas_configure(self, event) -> None:
        self.control_canvas.itemconfigure(self.control_canvas_window, width=event.width)

    def bind_control_mousewheel(self, _event=None) -> None:
        self.control_canvas.bind_all("<MouseWheel>", self.on_control_mousewheel)

    def unbind_control_mousewheel(self, _event=None) -> None:
        self.control_canvas.unbind_all("<MouseWheel>")

    def on_control_mousewheel(self, event) -> None:
        self.control_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def fit_control_window_to_content(self) -> None:
        self.root.update_idletasks()
        required_width = self.main_frame.winfo_reqwidth() + self.control_scrollbar.winfo_reqwidth() + 24
        required_height = self.main_frame.winfo_reqheight() + 24
        max_width = max(480, self.root.winfo_screenwidth() - 120)
        max_height = max(600, self.root.winfo_screenheight() - 120)
        width = min(max(540, required_width), max_width)
        height = min(max(700, required_height), max_height)
        self.root.geometry(f"{width}x{height}+80+80")
        self.on_control_main_frame_configure()

    def build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Show Timer Window", command=self.show_display_window)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_app_close)

        settings_menu = tk.Menu(menu_bar, tearoff=False)
        settings_menu.add_command(label="Appearance...", command=self.open_settings_window)
        settings_menu.add_checkbutton(
            label="Borderless Display",
            variable=self.borderless_var,
            command=self.apply_borderless_mode,
        )
        settings_menu.add_checkbutton(
            label="Display Always on Top",
            variable=self.always_on_top_var,
            command=self.apply_display_window_flags,
        )
        settings_menu.add_command(
            label="Restore Default Appearance", command=self.restore_default_appearance
        )

        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        self.root.config(menu=menu_bar)

    def build_control_panel(self) -> None:
        self.control_container = tk.Frame(self.root)
        self.control_container.pack(fill="both", expand=True)
        self.frame_widgets.append(self.control_container)

        self.control_canvas = tk.Canvas(
            self.control_container,
            highlightthickness=0,
            bd=0,
        )
        self.control_canvas.pack(side="left", fill="both", expand=True)

        self.control_scrollbar = tk.Scrollbar(
            self.control_container,
            orient="vertical",
            command=self.control_canvas.yview,
        )
        self.control_scrollbar.pack(side="right", fill="y")
        self.control_canvas.configure(yscrollcommand=self.control_scrollbar.set)

        self.main_frame = tk.Frame(self.control_canvas, padx=18, pady=18)
        self.control_canvas_window = self.control_canvas.create_window(
            (0, 0),
            window=self.main_frame,
            anchor="nw",
        )
        self.control_canvas.bind("<Configure>", self.on_control_canvas_configure)
        self.main_frame.bind("<Configure>", self.on_control_main_frame_configure)
        self.control_canvas.bind("<Enter>", self.bind_control_mousewheel)
        self.control_canvas.bind("<Leave>", self.unbind_control_mousewheel)

        self.frame_widgets.append(self.main_frame)

        self.title_label = tk.Label(
            self.main_frame,
            text="Speaker Timer Control Panel",
            anchor="w",
        )
        self.title_label.pack(fill="x")
        self.label_widgets.append(self.title_label)

        self.subtitle_label = tk.Label(
            self.main_frame,
            text="Set the countdown, start the session, and keep the display window visible for the presenter.",
            justify="left",
            wraplength=430,
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(6, 14))
        self.label_widgets.append(self.subtitle_label)

        self.active_timer_frame = tk.Frame(self.main_frame, padx=12, pady=12)
        self.active_timer_frame.pack(fill="x", pady=(0, 12))
        self.frame_widgets.append(self.active_timer_frame)
        self.panel_frame_widgets.append(self.active_timer_frame)

        self.active_timer_label = tk.Label(
            self.active_timer_frame,
            text="Active timer:",
            anchor="w",
        )
        self.active_timer_label.pack(side="left")
        self.label_widgets.append(self.active_timer_label)

        for speaker_key in self.speaker_order:
            speaker_state = self.get_speaker_state(speaker_key)
            radio = tk.Radiobutton(
                self.active_timer_frame,
                text=speaker_state["short_label"],
                variable=self.active_speaker_var,
                value=speaker_key,
                command=self.on_active_speaker_changed,
                anchor="w",
            )
            radio.pack(side="left", padx=(12, 0))
            self.radio_widgets.append(radio)

        self.setup_frame = tk.LabelFrame(self.main_frame, text="Timer Setup", padx=12, pady=12)
        self.setup_frame.pack(fill="x", pady=(0, 12))
        self.frame_widgets.append(self.setup_frame)

        self.setup_notebook = ttk.Notebook(self.setup_frame)
        self.setup_notebook.pack(fill="x", pady=(12, 0))

        for speaker_key in self.speaker_order:
            speaker_state = self.get_speaker_state(speaker_key)
            tab_frame = tk.Frame(self.setup_notebook, padx=12, pady=12)
            self.setup_notebook.add(tab_frame, text=speaker_state["label"])
            self.frame_widgets.append(tab_frame)
            self.panel_frame_widgets.append(tab_frame)
            self.build_speaker_setup_tab(tab_frame, speaker_key)

        self.controls_frame = tk.LabelFrame(
            self.main_frame, text="Timer Controls", padx=12, pady=12
        )
        self.controls_frame.pack(fill="x", pady=(0, 12))
        self.frame_widgets.append(self.controls_frame)

        self.start_button = self.make_button(
            self.controls_frame, "Start", self.start_timer, "start_button_bg", 11
        )
        self.start_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.stop_button = self.make_button(
            self.controls_frame, "Stop", self.stop_timer, "stop_button_bg", 11
        )
        self.stop_button.grid(row=0, column=1, padx=8, sticky="ew")

        self.reset_button = self.make_button(
            self.controls_frame, "Reset", self.reset_timer, "reset_button_bg", 11
        )
        self.reset_button.grid(row=0, column=2, padx=(8, 0), sticky="ew")

        self.add_minute_button = self.make_button(
            self.controls_frame,
            "+1 Min",
            lambda: self.adjust_time_by_minutes(1),
            "utility_button_bg",
            11,
        )
        self.add_minute_button.grid(row=1, column=0, padx=(0, 8), pady=(12, 0), sticky="ew")

        self.subtract_minute_button = self.make_button(
            self.controls_frame,
            "-1 Min",
            lambda: self.adjust_time_by_minutes(-1),
            "utility_button_bg",
            11,
        )
        self.subtract_minute_button.grid(
            row=1, column=1, padx=8, pady=(12, 0), sticky="ew"
        )

        self.show_timer_button = self.make_button(
            self.controls_frame,
            "Show Timer Window",
            self.show_display_window,
            "utility_button_bg",
            15,
        )
        self.show_timer_button.grid(
            row=1, column=2, padx=(8, 0), pady=(12, 0), sticky="ew"
        )

        for column in range(3):
            self.controls_frame.grid_columnconfigure(column, weight=1)

        self.status_frame = tk.LabelFrame(self.main_frame, text="Status", padx=12, pady=12)
        self.status_frame.pack(fill="x")
        self.frame_widgets.append(self.status_frame)

        self.status_label = tk.Label(self.status_frame, text="Current display")
        self.status_label.pack(anchor="w")
        self.label_widgets.append(self.status_label)

        self.current_time_label = tk.Label(
            self.status_frame,
            textvariable=self.current_display_var,
            anchor="center",
        )
        self.current_time_label.pack(fill="x", pady=(8, 8))
        self.label_widgets.append(self.current_time_label)

        self.state_value_label = tk.Label(
            self.status_frame, textvariable=self.status_var, anchor="w"
        )
        self.state_value_label.pack(anchor="w")
        self.label_widgets.append(self.state_value_label)

        self.keyboard_hint = tk.Label(
            self.status_frame,
            text="Shortcuts: Space = Start/Stop, Ctrl+R = Reset, Up/Down = +/- 1 minute",
            anchor="w",
        )
        self.keyboard_hint.pack(anchor="w", pady=(8, 0))
        self.label_widgets.append(self.keyboard_hint)

    def build_speaker_setup_tab(self, parent: tk.Frame, speaker_key: str) -> None:
        speaker_state = self.get_speaker_state(speaker_key)

        start_time_label = tk.Label(parent, text="Start time (MM:SS or HH:MM:SS)")
        start_time_label.grid(row=0, column=0, sticky="w")
        self.label_widgets.append(start_time_label)

        time_entry = tk.Entry(
            parent,
            textvariable=speaker_state["time_var"],
            width=16,
            justify="center",
        )
        time_entry.grid(row=1, column=0, sticky="w", pady=(4, 10))
        self.entry_widgets.append(time_entry)

        set_time_button = self.make_button(
            parent,
            "Apply Time",
            lambda key=speaker_key: self.apply_time_entry(key),
            "utility_button_bg",
            12,
        )
        set_time_button.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 10))

        warning_label = tk.Label(parent, text="Warning threshold")
        warning_label.grid(row=2, column=0, sticky="w")
        self.label_widgets.append(warning_label)

        warning_entry = tk.Entry(
            parent,
            textvariable=speaker_state["warning_var"],
            width=16,
            justify="center",
        )
        warning_entry.grid(row=3, column=0, sticky="w", pady=(4, 0))
        self.entry_widgets.append(warning_entry)

        set_warning_button = self.make_button(
            parent,
            "Apply Warning",
            lambda key=speaker_key: self.apply_warning_entry(key),
            "utility_button_bg",
            12,
        )
        set_warning_button.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))

        setup_hint = tk.Label(
            parent,
            text="Digits stay green above the warning time, turn yellow at the warning threshold, and turn red at 00:00 and into overtime.",
            justify="left",
            wraplength=390,
            anchor="w",
        )
        setup_hint.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.label_widgets.append(setup_hint)

        time_entry.bind("<Return>", lambda _event, key=speaker_key: self.apply_time_entry(key))
        warning_entry.bind(
            "<Return>",
            lambda _event, key=speaker_key: self.apply_warning_entry(key),
        )

    def on_active_speaker_changed(self) -> None:
        self.refresh_clock_faces()

    def build_display_window(self) -> None:
        self.display = tk.Toplevel(self.root)
        self.display.title("Speaker Timer Display")
        self.display.geometry(self.window_settings["display_geometry"])
        self.display.minsize(500, 220)
        self.display.protocol("WM_DELETE_WINDOW", self.hide_display_window)
        self.apply_window_icon(self.display)

        self.display_frame = tk.Frame(self.display, padx=20, pady=20)
        self.display_frame.pack(fill="both", expand=True)
        self.frame_widgets.append(self.display_frame)

        self.display_time_label = tk.Label(
            self.display_frame,
            textvariable=self.current_display_var,
            anchor="center",
        )
        self.display_time_label.pack(fill="both", expand=True)
        self.label_widgets.append(self.display_time_label)
        self.display.bind("<Configure>", self.handle_display_resize)

        for widget in (self.display, self.display_frame, self.display_time_label):
            widget.bind("<ButtonPress-1>", self.start_drag_display)
            widget.bind("<B1-Motion>", self.drag_display)

    def bind_shortcuts(self) -> None:
        self.root.bind("<space>", lambda _event: self.toggle_start_stop())
        self.root.bind("<Control-r>", lambda _event: self.reset_timer())
        self.root.bind("<Up>", lambda _event: self.adjust_time_by_minutes(1))
        self.root.bind("<Down>", lambda _event: self.adjust_time_by_minutes(-1))
        self.display.bind("<space>", lambda _event: self.toggle_start_stop())
        self.display.bind("<Control-r>", lambda _event: self.reset_timer())
        self.display.bind("<Up>", lambda _event: self.adjust_time_by_minutes(1))
        self.display.bind("<Down>", lambda _event: self.adjust_time_by_minutes(-1))
        self.display.bind("<Escape>", lambda _event: self.disable_borderless())

    def make_button(
        self,
        parent: tk.Misc,
        text: str,
        command,
        color_key: str,
        width: int,
    ) -> tk.Button:
        button = tk.Button(parent, text=text, command=command, width=width, relief="flat")
        self.button_styles.append((button, color_key))
        return button

    def open_settings_window(self) -> None:
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.deiconify()
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Appearance Settings")
        self.settings_window.geometry("540x520+160+140")
        self.settings_window.minsize(500, 460)
        self.settings_window.transient(self.root)
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)
        self.apply_window_icon(self.settings_window)

        container = tk.Frame(self.settings_window, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        title = tk.Label(
            container,
            text="Colors and Fonts",
            anchor="w",
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w")

        description = tk.Label(
            container,
            text="Use the pickers below to change the control panel and timer display colors at runtime.",
            wraplength=460,
            justify="left",
            anchor="w",
        )
        description.grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 14))

        color_rows = [
            ("Control background", "control_bg"),
            ("Panel background", "panel_bg"),
            ("Display background", "display_bg"),
            ("Normal digits", "normal_digits"),
            ("Warning digits", "warning_digits"),
            ("Overtime digits", "overtime_digits"),
            ("Start button", "start_button_bg"),
            ("Stop button", "stop_button_bg"),
            ("Reset button", "reset_button_bg"),
            ("Utility buttons", "utility_button_bg"),
        ]

        self.settings_controls = {}
        row_index = 2
        for label_text, palette_key in color_rows:
            label = tk.Label(container, text=label_text, anchor="w")
            label.grid(row=row_index, column=0, sticky="w", pady=4)
            value_var = tk.StringVar(value=self.palette[palette_key])
            value_label = tk.Label(container, textvariable=value_var, width=12, anchor="w")
            value_label.grid(row=row_index, column=1, sticky="w", padx=(10, 10))
            picker_button = tk.Button(
                container,
                text="Choose...",
                command=lambda key=palette_key, var=value_var: self.choose_color(key, var),
                relief="flat",
                width=12,
            )
            picker_button.grid(row=row_index, column=2, sticky="ew", pady=4)
            self.settings_controls[palette_key] = (value_var, value_label, picker_button)
            row_index += 1

        families = sorted(set(font.families()))
        self.control_font_family_var = tk.StringVar(
            value=self.font_settings["control_family"]
        )
        self.control_font_size_var = tk.StringVar(
            value=str(self.font_settings["control_size"])
        )
        self.digit_font_family_var = tk.StringVar(value=self.font_settings["digit_family"])
        self.digit_scale_var = tk.StringVar(value=str(self.font_settings["digit_scale"]))

        control_font_label = tk.Label(container, text="Control font", anchor="w")
        control_font_label.grid(row=row_index, column=0, sticky="w", pady=(14, 4))
        control_font_menu = tk.OptionMenu(
            container,
            self.control_font_family_var,
            self.control_font_family_var.get(),
            *families,
        )
        control_font_menu.grid(
            row=row_index, column=1, columnspan=2, sticky="ew", pady=(14, 4)
        )

        row_index += 1
        control_size_label = tk.Label(container, text="Control font size", anchor="w")
        control_size_label.grid(row=row_index, column=0, sticky="w", pady=4)
        control_size_spin = tk.Spinbox(
            container, from_=8, to=24, textvariable=self.control_font_size_var, width=10
        )
        control_size_spin.grid(row=row_index, column=1, sticky="w", pady=4)

        row_index += 1
        digit_font_label = tk.Label(container, text="Digit font", anchor="w")
        digit_font_label.grid(row=row_index, column=0, sticky="w", pady=(14, 4))
        digit_font_menu = tk.OptionMenu(
            container,
            self.digit_font_family_var,
            self.digit_font_family_var.get(),
            *families,
        )
        digit_font_menu.grid(row=row_index, column=1, columnspan=2, sticky="ew", pady=(14, 4))

        row_index += 1
        digit_scale_label = tk.Label(container, text="Digit height %", anchor="w")
        digit_scale_label.grid(row=row_index, column=0, sticky="w", pady=4)
        digit_scale_spin = tk.Spinbox(
            container,
            from_=50,
            to=95,
            increment=1,
            textvariable=self.digit_scale_var,
            width=10,
        )
        digit_scale_spin.grid(row=row_index, column=1, sticky="w", pady=4)

        row_index += 1
        apply_button = tk.Button(
            container, text="Apply Fonts", command=self.apply_font_changes, relief="flat"
        )
        apply_button.grid(row=row_index, column=0, sticky="ew", pady=(18, 0))

        defaults_button = tk.Button(
            container,
            text="Restore Defaults",
            command=self.restore_default_appearance,
            relief="flat",
        )
        defaults_button.grid(row=row_index, column=1, sticky="ew", padx=10, pady=(18, 0))

        close_button = tk.Button(
            container,
            text="Close",
            command=self.close_settings_window,
            relief="flat",
        )
        close_button.grid(row=row_index, column=2, sticky="ew", pady=(18, 0))

        for widget in container.winfo_children():
            if isinstance(widget, tk.Label):
                self.label_widgets.append(widget)
            elif isinstance(widget, tk.Button):
                self.button_styles.append((widget, "utility_button_bg"))

        container.grid_columnconfigure(1, weight=1)
        container.grid_columnconfigure(2, weight=1)
        self.frame_widgets.append(container)
        self.apply_theme()

    def close_settings_window(self) -> None:
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.destroy()
        self.settings_window = None

    def choose_color(self, palette_key: str, value_var: tk.StringVar) -> None:
        color = colorchooser.askcolor(
            initialcolor=self.palette[palette_key],
            title=f"Choose {palette_key.replace('_', ' ')}",
            parent=self.settings_window,
        )[1]
        if not color:
            return
        self.palette[palette_key] = color
        value_var.set(color)
        self.apply_theme()
        self.refresh_clock_faces()

    def apply_font_changes(self) -> None:
        try:
            control_size = int(self.control_font_size_var.get())
            digit_scale = int(self.digit_scale_var.get())
        except ValueError:
            messagebox.showerror("Invalid Font Setting", "Font values must be whole numbers.")
            return

        if not 50 <= digit_scale <= 95:
            messagebox.showerror(
                "Invalid Digit Scale",
                "Digit height % must be between 50 and 95.",
            )
            return

        self.font_settings["control_family"] = self.control_font_family_var.get()
        self.font_settings["control_size"] = control_size
        self.font_settings["digit_family"] = self.digit_font_family_var.get()
        self.font_settings["digit_scale"] = digit_scale
        self.apply_theme()
        self.refresh_clock_faces()

    def restore_default_appearance(self) -> None:
        self.palette = DEFAULT_PALETTE.copy()
        self.font_settings = DEFAULT_FONTS.copy()
        self.borderless_var.set(DEFAULT_WINDOW["borderless_display"])
        self.always_on_top_var.set(DEFAULT_WINDOW["display_always_on_top"])

        if self.settings_window and self.settings_window.winfo_exists():
            for palette_key, control_set in self.settings_controls.items():
                control_set[0].set(self.palette[palette_key])
            self.control_font_family_var.set(self.font_settings["control_family"])
            self.control_font_size_var.set(str(self.font_settings["control_size"]))
            self.digit_font_family_var.set(self.font_settings["digit_family"])
            self.digit_scale_var.set(str(self.font_settings["digit_scale"]))

        self.apply_theme()
        self.refresh_clock_faces()
        self.apply_display_window_flags()

    def apply_theme(self) -> None:
        control_font = (
            self.font_settings["control_family"],
            self.font_settings["control_size"],
        )
        title_font = (
            self.font_settings["control_family"],
            self.font_settings["control_size"] + 4,
            "bold",
        )
        status_font = (
            self.font_settings["digit_family"],
            36,
            "bold",
        )

        self.root.configure(bg=self.palette["control_bg"])
        self.control_container.configure(bg=self.palette["control_bg"])
        self.control_canvas.configure(bg=self.palette["control_bg"])
        self.main_frame.configure(bg=self.palette["control_bg"])
        self.display.configure(bg=self.palette["display_bg"])
        self.display_frame.configure(bg=self.palette["display_bg"])

        panel_masters = {
            self.setup_frame,
            self.controls_frame,
            self.status_frame,
        }

        for frame in self.frame_widgets:
            if not frame.winfo_exists():
                continue
            if isinstance(frame, tk.LabelFrame):
                frame.configure(
                    bg=self.palette["panel_bg"],
                    fg=self.palette["control_fg"],
                    bd=1,
                    highlightbackground=self.palette["panel_border"],
                    highlightcolor=self.palette["panel_border"],
                    highlightthickness=1,
                    font=control_font,
                )
            elif frame in self.panel_frame_widgets:
                frame.configure(bg=self.palette["panel_bg"])
            elif frame is self.display_frame:
                frame.configure(bg=self.palette["display_bg"])
            else:
                frame.configure(bg=self.palette["control_bg"])

        for label in self.label_widgets:
            if not label.winfo_exists():
                continue
            if label is self.display_time_label:
                continue
            label_bg = (
                self.palette["panel_bg"]
                if label.master in panel_masters or label.master in self.panel_frame_widgets
                else self.palette["control_bg"]
            )
            label.configure(
                bg=label_bg,
                fg=self.palette["control_fg"],
                font=control_font,
            )

        self.title_label.configure(
            bg=self.palette["control_bg"], fg=self.palette["control_fg"], font=title_font
        )
        self.subtitle_label.configure(
            bg=self.palette["control_bg"], fg=self.palette["status_text"], font=control_font
        )
        self.keyboard_hint.configure(
            bg=self.palette["panel_bg"], fg=self.palette["status_text"], font=control_font
        )
        self.state_value_label.configure(
            bg=self.palette["panel_bg"], fg=self.palette["status_text"], font=control_font
        )

        self.current_time_label.configure(
            bg=self.palette["panel_bg"],
            font=status_font,
        )

        for entry in self.entry_widgets:
            if not entry.winfo_exists():
                continue
            entry.configure(
                bg=self.palette["entry_bg"],
                fg=self.palette["entry_fg"],
                insertbackground=self.palette["entry_fg"],
                relief="flat",
                font=control_font,
            )

        for check in self.check_widgets:
            if not check.winfo_exists():
                continue
            check.configure(
                bg=self.palette["panel_bg"],
                fg=self.palette["control_fg"],
                activebackground=self.palette["panel_bg"],
                activeforeground=self.palette["control_fg"],
                selectcolor=self.palette["panel_bg"],
                font=control_font,
            )

        for radio in self.radio_widgets:
            if not radio.winfo_exists():
                continue
            radio.configure(
                bg=self.palette["panel_bg"],
                fg=self.palette["control_fg"],
                activebackground=self.palette["panel_bg"],
                activeforeground=self.palette["control_fg"],
                selectcolor=self.palette["panel_bg"],
                font=control_font,
            )

        for button, color_key in self.button_styles:
            if not button.winfo_exists():
                continue
            button.configure(
                bg=self.palette[color_key],
                fg=self.palette["button_fg"],
                activebackground=self.palette[color_key],
                activeforeground=self.palette["button_fg"],
                font=control_font,
                bd=0,
                padx=10,
                pady=8,
            )

        self.display_time_label.configure(bg=self.palette["display_bg"])
        self.update_display_font()
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.configure(bg=self.palette["control_bg"])

    def handle_display_resize(self, _event=None) -> None:
        self.update_display_font()

    def update_display_font(self) -> None:
        if not self.display_time_label.winfo_exists():
            return

        active_state = self.get_speaker_state()
        available_height = max(1, self.display_frame.winfo_height())
        available_width = max(1, self.display_frame.winfo_width())
        target_height = max(
            48,
            int(available_height * (self.font_settings["digit_scale"] / 100)),
        )

        max_seconds = max(
            abs(active_state["current_remaining_seconds"]),
            active_state["duration_seconds"],
        )
        sample_text = "-88:88:88" if max_seconds >= 3600 else "-88:88"
        probe_font = font.Font(
            family=self.font_settings["digit_family"],
            size=-100,
            weight="bold",
        )
        probe_height = max(1, probe_font.metrics("linespace"))
        probe_width = max(1, probe_font.measure(sample_text))

        height_fit = int((target_height / probe_height) * 100)
        width_fit = int(((available_width * 0.95) / probe_width) * 100)
        pixel_size = max(36, min(height_fit, width_fit))

        self.display_time_label.configure(
            font=(self.font_settings["digit_family"], -pixel_size, "bold")
        )

    def apply_time_entry(self, speaker_key=None, sync_current: bool = True) -> bool:
        speaker_state = self.get_speaker_state(speaker_key)
        try:
            seconds = self.parse_time_input(speaker_state["time_var"].get())
        except ValueError as exc:
            messagebox.showerror("Invalid Time", str(exc))
            return False

        previous_duration = speaker_state["duration_seconds"]
        speaker_state["duration_seconds"] = seconds
        should_sync_current = sync_current
        if not sync_current and not speaker_state["timer_running"]:
            should_sync_current = (
                abs(speaker_state["current_remaining_seconds"] - previous_duration) < 0.5
                or speaker_state["current_remaining_seconds"] <= 0
            )

        if not speaker_state["timer_running"] and should_sync_current:
            speaker_state["current_remaining_seconds"] = float(seconds)
        if (speaker_key or self.active_speaker_var.get()) == self.active_speaker_var.get():
            self.refresh_clock_faces()
        return True

    def apply_warning_entry(self, speaker_key=None) -> bool:
        speaker_state = self.get_speaker_state(speaker_key)
        try:
            seconds = self.parse_time_input(speaker_state["warning_var"].get())
        except ValueError as exc:
            messagebox.showerror("Invalid Warning Threshold", str(exc))
            return False

        speaker_state["warning_seconds"] = seconds
        if (speaker_key or self.active_speaker_var.get()) == self.active_speaker_var.get():
            self.refresh_clock_faces()
        return True

    def start_timer(self) -> None:
        active_key = self.active_speaker_var.get()
        active_state = self.get_speaker_state(active_key)
        if not self.apply_time_entry(active_key, sync_current=False) or not self.apply_warning_entry(active_key):
            return
        if active_state["timer_running"]:
            return
        active_state["timer_running"] = True
        active_state["end_monotonic"] = time.monotonic() + active_state["current_remaining_seconds"]
        self.refresh_clock_faces()

    def stop_timer(self) -> None:
        active_state = self.get_speaker_state()
        if not active_state["timer_running"]:
            return
        active_state["current_remaining_seconds"] = active_state["end_monotonic"] - time.monotonic()
        active_state["timer_running"] = False
        self.refresh_clock_faces()

    def reset_timer(self) -> None:
        active_key = self.active_speaker_var.get()
        active_state = self.get_speaker_state(active_key)
        if not self.apply_time_entry(active_key) or not self.apply_warning_entry(active_key):
            return
        active_state["timer_running"] = False
        active_state["current_remaining_seconds"] = float(active_state["duration_seconds"])
        self.refresh_clock_faces()

    def toggle_start_stop(self) -> None:
        if self.get_speaker_state()["timer_running"]:
            self.stop_timer()
        else:
            self.start_timer()

    def adjust_time_by_minutes(self, minute_delta: int) -> None:
        active_state = self.get_speaker_state()
        seconds_delta = minute_delta * 60
        if active_state["timer_running"]:
            active_state["end_monotonic"] += seconds_delta
            active_state["current_remaining_seconds"] = (
                active_state["end_monotonic"] - time.monotonic()
            )
        else:
            active_state["current_remaining_seconds"] = max(
                0.0, active_state["current_remaining_seconds"] + seconds_delta
            )
        self.refresh_clock_faces()

    def update_timer_loop(self) -> None:
        active_key = self.active_speaker_var.get()
        refresh_needed = False
        for speaker_key, speaker_state in self.speaker_data.items():
            if not speaker_state["timer_running"]:
                continue
            speaker_state["current_remaining_seconds"] = (
                speaker_state["end_monotonic"] - time.monotonic()
            )
            if speaker_key == active_key:
                refresh_needed = True

        if refresh_needed:
            self.refresh_clock_faces()
        self.update_job = self.root.after(100, self.update_timer_loop)

    def refresh_clock_faces(self) -> None:
        active_state = self.get_speaker_state()
        speaker_label = active_state["label"]
        seconds = active_state["current_remaining_seconds"]
        display_text = self.format_time_for_display(seconds)
        color = self.get_timer_color(seconds)

        self.current_display_var.set(display_text)
        self.display_time_label.configure(fg=color)
        self.current_time_label.configure(fg=color)
        self.update_display_font()
        self.status_label.configure(text=f"Current display ({speaker_label} active)")

        if active_state["timer_running"]:
            self.status_var.set(f"{speaker_label} running")
        elif seconds < 0:
            self.status_var.set(f"{speaker_label} stopped in overtime")
        elif seconds == 0:
            self.status_var.set(f"{speaker_label} time up")
        else:
            self.status_var.set(f"{speaker_label} stopped")

    def get_timer_color(self, seconds: float) -> str:
        active_state = self.get_speaker_state()
        if seconds <= 0:
            return self.palette["overtime_digits"]
        if seconds <= active_state["warning_seconds"]:
            return self.palette["warning_digits"]
        return self.palette["normal_digits"]

    def parse_time_input(self, raw_value: str) -> int:
        value = raw_value.strip()
        if not value:
            raise ValueError("Enter a time such as 15, 15:00, or 1:15:00.")

        parts = value.split(":")
        try:
            numbers = [int(part) for part in parts]
        except ValueError as exc:
            raise ValueError("Use only numbers separated by colons.") from exc

        if len(numbers) == 1:
            minutes = numbers[0]
            if minutes < 0:
                raise ValueError("Time cannot be negative.")
            return minutes * 60

        if len(numbers) == 2:
            minutes, seconds = numbers
            if minutes < 0 or seconds < 0 or seconds >= 60:
                raise ValueError("Use MM:SS with seconds between 00 and 59.")
            return (minutes * 60) + seconds

        if len(numbers) == 3:
            hours, minutes, seconds = numbers
            if (
                hours < 0
                or minutes < 0
                or seconds < 0
                or minutes >= 60
                or seconds >= 60
            ):
                raise ValueError("Use HH:MM:SS with minutes and seconds between 00 and 59.")
            return (hours * 3600) + (minutes * 60) + seconds

        raise ValueError("Use one of these formats: MM, MM:SS, or HH:MM:SS.")

    def format_time_for_entry(self, total_seconds: int) -> str:
        total_seconds = max(0, int(total_seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def format_time_for_display(self, seconds: float) -> str:
        if seconds >= 0:
            absolute_seconds = max(0, math.ceil(seconds))
            sign = ""
        else:
            absolute_seconds = int(abs(seconds))
            sign = "-"

        hours, remainder = divmod(absolute_seconds, 3600)
        minutes, seconds_value = divmod(remainder, 60)
        if hours:
            return f"{sign}{hours}:{minutes:02d}:{seconds_value:02d}"
        return f"{sign}{minutes:02d}:{seconds_value:02d}"

    def show_display_window(self) -> None:
        self.display.deiconify()
        self.display.attributes("-topmost", self.always_on_top_var.get())
        self.display.lift()

    def apply_display_window_flags(self) -> None:
        if not self.display.winfo_exists():
            return

        try:
            was_hidden = self.display.state() == "withdrawn"
        except tk.TclError:
            was_hidden = False

        try:
            current_geometry = self.display.geometry()
        except tk.TclError:
            current_geometry = None

        try:
            self.display.withdraw()
            self.display.overrideredirect(self.borderless_var.get())
            self.display.attributes("-topmost", self.always_on_top_var.get())
            if current_geometry:
                self.display.geometry(current_geometry)
            if not was_hidden:
                self.display.deiconify()
                self.display.lift()
        except tk.TclError:
            pass

    def hide_display_window(self) -> None:
        self.display.withdraw()

    def apply_borderless_mode(self) -> None:
        self.apply_display_window_flags()

    def disable_borderless(self) -> None:
        if not self.borderless_var.get():
            return
        self.borderless_var.set(False)
        self.apply_borderless_mode()

    def start_drag_display(self, event) -> None:
        if not self.borderless_var.get():
            return
        self.drag_offset_x = event.x_root - self.display.winfo_x()
        self.drag_offset_y = event.y_root - self.display.winfo_y()

    def drag_display(self, event) -> None:
        if not self.borderless_var.get():
            return
        new_x = event.x_root - self.drag_offset_x
        new_y = event.y_root - self.drag_offset_y
        self.display.geometry(f"+{new_x}+{new_y}")

    def on_app_close(self) -> None:
        if self.update_job:
            self.root.after_cancel(self.update_job)
        self.display.destroy()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    SpeakerTimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
