import queue
import threading
from aqt import mw
from aqt.qt import *
from aqt.gui_hooks import profile_did_open, profile_will_close, reviewer_did_answer_card

from .llm import LLM

from .anki import Anki, derive_fields
import re
import os, sys
from contextlib import contextmanager


@contextmanager
def silence_stderr():
    new_target = open(os.devnull, "w")
    old_target = sys.stderr
    sys.stderr = new_target
    try:
        yield
    finally:
        sys.stderr = old_target
        new_target.close()


class BackgroundTask(threading.Thread):
    def __init__(self, cfg, models_path):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()
        self.cfg = cfg
        self.models_path = models_path
        self.msg_queue = queue.LifoQueue()
        self.do_sync = False
        self.llm = None

    def stop(self):
        if self.llm:
            self.llm.close()
        self._stop_event.set()

    def run(self):
        mw.taskman.run_on_main(Anki.get_or_create_custom_model)

        dictionary, cards = Anki.load_dictionary(self.cfg["decks"])
        for form in self.cfg["forms"]:
            dictionary.forms.add(form)

        with silence_stderr():
            self.llm = LLM(self.cfg["output"]["dialect"], dictionary,
                           local_dir=self.models_path, **self.cfg["model"])

        print("Background llm thread: Started listening.")
        while not self._stop_event.is_set():
            try:
                message = self.msg_queue.get(timeout=1.0)

                if message["action"] == "update_all":
                    mw.taskman.run_on_main(self.update_all)
                    self.do_sync = True
                if message["action"] in ["review", "update"]:
                    self.update_card(message["card"])

                self.msg_queue.task_done()
                if self.msg_queue.qsize() == 0 and self.do_sync:
                    mw.taskman.run_on_main(mw.onSync)
                    self.do_sync = False

            except queue.Empty:
                continue

    def update_all(self):

        snapshot = list(self.msg_queue.queue)
        _, cards = Anki.load_dictionary(self.cfg["decks"])
        for card in cards:
            if card["modelName"] == "anki-greek" and card["mod"] > card["reviewed"]:
                continue

            msg = {"action": "update", "card": card}
            if msg not in snapshot:
                self.msg_queue.put(msg)

    def update_card(self, card):
        mw.taskman.run_on_main(mw.toolbar.draw)

        if card["modelName"] == "anki-greek" and "reviewed" in card and "mod" in card and card["mod"] > card["reviewed"]:
            return

        print("updating", card["word"], "-",
              card["definition"], f"({card["form"]})")

        self.llm.dictionary.add(card)

        story, translation = self.llm.generate(
            card["word"], card["entry"], card["definition"], length=self.cfg["output"]["length"], dict_limit=20)

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
            print("Anki closing: Stopping background thread...")
            _listener.stop()
            _listener.join(timeout=5.0)
            _listener = None

    def get_llm_msg_queue():
        nonlocal _listener
        if _listener:
            return _listener.msg_queue

    def on_review(reviewer, card, ease):
        q = get_llm_msg_queue()
        key = mw.col.decks.name(card.did)
        if q and any([re.match(deck+"$", key) for deck in cfg["decks"]]):
            q.put({"action": "review", "card": derive_fields(card.note())})

    profile_did_open.append(start_listener)
    profile_will_close.append(stop_listener)
    reviewer_did_answer_card.append(on_review)

    return get_llm_msg_queue

