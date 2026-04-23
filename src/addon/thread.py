import queue
import threading
from aqt import mw
from aqt.qt import *
from aqt.gui_hooks import profile_did_open, profile_will_close, reviewer_did_answer_card

import json
from .deps import init

from .anki import Anki, derive_fields


class BackgroundTask(threading.Thread):
    def __init__(self, cfg, models_path):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()
        self.cfg = cfg
        self.models_path = models_path
        self.msg_queue = queue.Queue()
        self.do_sync = False
        self.llms = {}

    def stop(self):
        self._stop_event.set()
        self.msg_queue.shutdown(immediate=True)
        for llm in self.llms.values():
            llm.close()

    def get_llm(self, cfg):

        key = json.dumps(cfg)
        if key in self.llms:
            return self.llms[key]
        
        dictionary = Anki.load_dict([d["name"] for d in Anki.list_decks_by_config(cfg["id"])])
        print(f"anki-greek: loaded dictionary for model: {len(dictionary.nouns)} nouns, {len(dictionary.verbs)} verbs.")

        print(f"anki-greek: loading model {cfg.get("model", {}).get("repo", "")}.")
        from generator import LLM

        llm = LLM(cfg["dialect"], dictionary, cfg["verb_moods"],
                        local_dir=self.models_path, **cfg["model"])
        
        self.llms[key] = llm
        return llm

    def run(self):
        mw.taskman.run_on_main(Anki.get_or_create_custom_model)

        print("anki-greek: started background thread.")

        init()
        
        while not self._stop_event.is_set():
            try:
                message = self.msg_queue.get(timeout=1.0)

                if message["action"] == "update_all":
                    mw.taskman.run_on_main(self.update_all)
                    self.do_sync = True
                if message["action"] == "update_deck":
                    mw.taskman.run_on_main(lambda: self.update_deck(message["deck"]))
                    self.do_sync = True
                if message["action"] in ["review", "update"]:
                    self.update_card(message["card"], message["cfg"])

                    if self.msg_queue.qsize() == 0 and self.do_sync:
                        mw.taskman.run_on_main(mw.onSync)
                        self.do_sync = False

                self.msg_queue.task_done()

            except queue.Empty:
                continue

            except queue.ShutDown:
                return

    def update_all(self):

        cfgs = {}

        snapshot = list(self.msg_queue.queue)
        cards = Anki.get_card_info(Anki.list_cards("anki-greek", query="note"))
        for card in cards:
            if card["modelName"] == "anki-greek" and card["mod"] > card["reviewed"]:
                continue

            cfg_id = card["deck_conf"]
            if not cfg_id in cfgs:
                cfgs[cfg_id] = Anki.get_review_config(cfg_id)

            if not cfgs[cfg_id].get("enabled", False):
                continue

            msg = {"action": "update", "card": card, "cfg": cfgs[cfg_id]}
            if msg not in snapshot:
                self.msg_queue.put(msg)
    
    def update_deck(self, deck_id):

        deck = mw.col.decks.get(deck_id)
        cfg = Anki.get_review_config(deck.get("conf"))
        if not cfg.get("enabled", False):
            return
        
        print("anki-greek: updating deck", deck_id, deck["name"])

        cards = Anki.get_card_info(Anki.list_cards(deck["name"]))
        for card in cards:
            if card["modelName"] == "anki-greek" and "reviewed" in card and "mod" in card and card["mod"] > card["reviewed"]:
                continue
        
            msg = {"action": "update", "card": card, "cfg": cfg}
            self.msg_queue.put(msg)

    def update_card(self, card, cfg):
        mw.taskman.run_on_main(mw.toolbar.draw)

        if card["modelName"] == "anki-greek" and "reviewed" in card and "mod" in card and card["mod"] > card["reviewed"]:
            return

        print("anki-greek: updating", card["word"], "-",
              card["definition"], f"({card["form"]})", "-", cfg["dialect"])

        llm = self.get_llm(cfg)
        llm.dictionary.add(card)

        story, translation = llm.generate(
            card["word"], card["entry"], card["definition"], dict_limit=20)

        mw.taskman.run_on_main(lambda: Anki.update_card(card["noteId"], {
            "Story": story,
            "Translation": translation,
        }))

        mw.taskman.run_on_main(mw.toolbar.draw)


def setup_llm_thread(cfg, models_path):

    _listener = None

    def start_listener():
        nonlocal _listener
        if _listener is None:
            _listener = BackgroundTask(cfg, models_path)
            _listener.start()

    def stop_listener():
        nonlocal _listener
        if _listener:
            print("anki-greek: stopping background thread...")
            _listener.stop()
            _listener.join(timeout=30.0)
            _listener = None

    def get_llm_msg_queue():
        nonlocal _listener
        if _listener:
            return _listener.msg_queue

    def on_review(reviewer, card, ease):
        q = get_llm_msg_queue()
        if not q:
            return

        deck = mw.col.decks.get(card.did)
        conf = Anki.get_review_config(deck.get("conf"))
        if not conf["enabled"]:
            return

        crd = derive_fields(card.note(), deck)
        q.put({"action": "review", "card": crd, "cfg": conf})

    profile_did_open.append(start_listener)
    profile_will_close.append(stop_listener)
    reviewer_did_answer_card.append(on_review)

    return get_llm_msg_queue
