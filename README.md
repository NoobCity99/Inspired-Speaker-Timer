# Speaker Timer User Manual

## Overview
- This app provides two windows:
- `Control Panel`: where you set up speakers, manage countdowns, and change appearance settings.
- `Timer Display`: a large-format clock intended for the speaker or presenter to watch while speaking.

## Starting the App
- Run `TIMER.py` with Python to open the control panel and the timer display window.
- The control window opens with the full main interface visible when screen space allows.
- If the control panel is smaller than the full content, use the mouse wheel to scroll.

## Speaker Setup
- The app supports two independent speaker timers:
- `Speaker 1`
- `Speaker 2`
- Use the `SPKR 1` and `SPKR 2` radio buttons above `Timer Setup` to choose which speaker is the active live timer.
- Use the `Speaker 1` and `Speaker 2` tabs to prepare settings for each speaker independently.
- This lets you keep one speaker live while setting up the next speaker in advance.

## Entering Time
- Each speaker tab includes a `Start time` field.
- Accepted time formats are:
- `MM`
- `MM:SS`
- `HH:MM:SS`
- Examples:
- `15` means 15 minutes.
- `12:30` means 12 minutes 30 seconds.
- `1:05:00` means 1 hour 5 minutes.
- Click `Apply Time` to save the entered starting time for that speaker.

## Warning Threshold
- Each speaker tab includes a `Warning threshold` field.
- Enter the warning time in the same formats:
- `MM`
- `MM:SS`
- `HH:MM:SS`
- Click `Apply Warning` to save it.
- When the timer reaches the warning threshold, the display digits change from green to yellow.

## Timer Controls
- `Start`: begins the countdown for the active speaker.
- `Stop`: pauses the active speaker timer.
- `Reset`: restores the active speaker timer to its saved start time.
- `+1 Min`: adds one minute to the active speaker timer.
- `-1 Min`: subtracts one minute from the active speaker timer.
- `Show Timer Window`: brings the presenter display window to the front.

## Timer Display Behavior
- The timer display shows large countdown digits for the active speaker.
- The display color changes automatically:
- Green: more time than the warning threshold remains.
- Yellow: the timer has reached the warning threshold.
- Red: the timer has reached zero or gone beyond zero.
- When the countdown passes zero, the timer continues into overtime using negative time such as `-00:15`.
- The timer digits automatically resize to fit the display window as the window is resized.

## Active Speaker Workflow
- Only the speaker selected by the `SPKR 1` / `SPKR 2` radio buttons is considered the live timer.
- The large display window always follows the active speaker.
- You can configure the other speaker’s tab without changing the current live timer until you switch the radio selection.

## Keyboard Shortcuts
- `Space`: start or stop the active speaker timer.
- `Ctrl+R`: reset the active speaker timer.
- `Up Arrow`: add one minute to the active speaker timer.
- `Down Arrow`: subtract one minute from the active speaker timer.
- `Escape` in the display window: exit borderless mode.

## Settings Menu
- Open the `Settings` menu from the control panel menu bar.
- `Appearance...` opens the appearance settings window.
- `Borderless Display` toggles the timer display window border on or off.
- `Restore Default Appearance` resets colors and fonts to the built-in defaults.

## Appearance Settings
- You can change:
- Control panel background and panel colors.
- Timer display background color.
- Normal, warning, and overtime digit colors.
- Button colors.
- Control font family and size.
- Timer digit font family.
- Digit height percentage.
- `Digit height %` controls how tall the timer numbers appear relative to the display window height.

## Borderless Display
- Turn on `Borderless Display` from the `Settings` menu for a cleaner presenter-facing timer window.
- When borderless mode is enabled, click and drag inside the timer display window to move it.
- Press `Escape` inside the display window to quickly turn borderless mode off.

## Scrollable Control Panel
- If the control panel window is too short to show all content, the interface can be scrolled.
- Move the mouse pointer over the control panel and use the mouse wheel to scroll vertically.

## Custom Icons
- The project includes an `ICON` folder for custom icon files.
- `ICON/WIN.ico` is used for the app window icon when present.
- `ICON/DESK.ico` is reserved for future standalone packaged app builds.
- See [ICON/README.md](/c:/Users/Buckles/Documents/Python%20Projects/SpkrTmr/ICON/README.md) for the icon folder notes.

## Notes
- If an icon file is missing, the app still runs normally.
- Speaker 1 and Speaker 2 keep separate saved times and warning thresholds.
- The timer display and status panel always reflect the currently active speaker.
