import inspect
import os
debug_mode_enabled = False


def get_debug_mode():
    global debug_mode_enabled
    return debug_mode_enabled


def toggle_debug_mode():
    global debug_mode_enabled
    debug_mode_enabled = not debug_mode_enabled


def print_debug(*args, **kwargs):
    global debug_mode_enabled
    if not debug_mode_enabled:
        return
    # Get the current frame (f_back gives the previous frame where the print_with_location was called)
    frame = inspect.currentframe().f_back
    # Get the file name and line number
    file_name = frame.f_code.co_filename
    line_number = frame.f_lineno

    # Add the file name and line number to the output
    print(
        f"debug - {os.path.basename(file_name)}:{line_number} - ", *args, **kwargs)
