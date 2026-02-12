from aqt import mw
from aqt.qt import *
from aqt.gui_hooks import top_toolbar_did_init_links

from .deps import init
addon_path, vendor_path, models_path = init()

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

    # We use the toolbar's helper to create the link correctly
    # This ensures the styling matches the rest of the UI
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
