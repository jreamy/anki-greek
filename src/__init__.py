from aqt import mw
from aqt.qt import *
from aqt.gui_hooks import top_toolbar_did_init_links, deck_browser_will_show_options_menu
from aqt.utils import showInfo

from .deps import paths
addon_path, vendor_path, models_path = paths()

from .thread import setup_llm_thread

from .options import init_deck_options
init_deck_options()

cfg = mw.addonManager.getConfig(__name__)

get_llm_message_queue = setup_llm_thread(cfg, models_path)

def on_click_generate():
    get_llm_message_queue().put({"action": "update_all"})

def on_links_init(links, toolbar):
    q = get_llm_message_queue()
    q_size = q.unfinished_tasks if q else 0

    new_link = toolbar.create_link(
        "generate-btn",
        "Generate" if q_size < 2 else f"Generating ({q_size})",
        on_click_generate,
        tip="Click to start generating cards!",
        id="generate-button"
    )
    
    # Add it to the list of links (this places it near Sync)
    links.insert(-1, new_link)

# Register the correct hook
top_toolbar_did_init_links.append(on_links_init)

# Add a button to generate a specific deck
def on_gear_menu_created(menu: QMenu, deck_id: int):
    action = QAction("Generate", menu)    
    action.triggered.connect(lambda: get_llm_message_queue().put({"action": "update_deck", "deck": deck_id}))
    menu.addAction(action)

# Register the hook
deck_browser_will_show_options_menu.append(on_gear_menu_created)