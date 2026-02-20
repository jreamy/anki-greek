import json
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.deckoptions import DeckOptionsDialog

file = Path(__file__)

with open(file.with_name("options.html"), encoding="utf8") as f:
    html = f.read()
with open(file.with_name("options.js"), encoding="utf8") as f:
    script = f.read()

def on_mount(dialog: DeckOptionsDialog) -> None:
    dialog.web.eval(script.replace("HTML_CONTENT", json.dumps(html)))

def init_deck_options():
    gui_hooks.deck_options_did_load.append(on_mount)