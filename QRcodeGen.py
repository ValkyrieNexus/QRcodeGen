import adsk.core
import adsk.fusion
import traceback
import os
import sys
import importlib

# Add addon root and lib/ to path for imports
addon_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(addon_dir, 'lib')

for path in [addon_dir, lib_path]:
    if path not in sys.path:
        sys.path.insert(0, path)


def _reload_modules():
    """Delete all addon modules from cache so they get freshly imported."""
    to_delete = [
        name for name in list(sys.modules.keys())
        if name == 'config'
        or name.startswith('commands')
    ]
    for name in to_delete:
        del sys.modules[name]


def run(context):
    try:
        _reload_modules()
        from commands import start as commands_start
        commands_start()
    except Exception:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox(f'QRcodeGen failed to start:\n{traceback.format_exc()}')


def stop(context):
    try:
        from commands import stop as commands_stop
        commands_stop()
    except Exception:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox(f'QRcodeGen failed to stop:\n{traceback.format_exc()}')
