
import requests
import re
from dictionary import Dictionary

class Anki:

    def create_card(front, back, deck):
        return requests.post("http://localhost:8765", json={
            "action": "addNotes",
            "version": 5,
            "params": {
                "notes": [
                    {
                        "deckName": deck,
                        "modelName": "Basic",
                        "fields": {
                            "Front": front,
                            "Back": back
                        },
                        "tags": [
                            "generated",
                        ]
                    }
                ]
            }
        }).json()


    def tagged_cards():
        return requests.post("http://localhost:8765", json={
            "action": "findNotes",
            "version": 5,
            "params": {
                "query": "tag:generated"
            }
        }).json()["result"]


    def list_cards(deck):
        return requests.post("http://localhost:8765", json={
            "action": "findNotes",
            "version": 5,
            "params": {
                "query": f"deck:{deck}"
            }
        }).json()["result"]


    def card_info(ids):
        return requests.post("http://localhost:8765", json={
            "action": "notesInfo",
            "version": 5,
            "params": {
                "notes": ids
            }
        }).json()["result"]


    def update_card(id, fields):
        return requests.post("http://localhost:8765", json={
            "action": "updateNoteFields",
            "version": 5,
            "params": {
                "note": {
                    "id": id,
                    "fields": fields,
                }
            }
        }).json()["result"]


    def get_revlog(ids):
        return requests.post("http://localhost:8765", json={
            "action": "getReviewsOfCards",
            "version": 5,
            "params": {
                "cards": ids,
            }
        }).json()["result"]


    def add_tags(ids, tags):
        return requests.post("http://localhost:8765", json={
            "action": "addTags",
            "version": 5,
            "params": {
                "notes": ids,
                "tags": tags,
            }
        }).json()


    def list_decks():
        return requests.post("http://localhost:8765", json={
            "action": "deckNamesAndIds",
            "version": 5,
        }).json()["result"]


    def get_card_info(ids):
        cards = Anki.card_info(ids)
        reviews = Anki.get_revlog([c for card in cards for c in card["cards"]])

        for card in cards:
            revs = [r for c in card["cards"] for r in reviews[str(c)]]
            card["reviewed"] = int(max([int(x["id"])
                                for x in revs]) / 1000) if len(revs) else 0

            card["entry"] = card["fields"]["Front"]["value"].split(
                "<br/>")[-1].split("<br>")[-1].strip().strip("[]")
            card["word"] = card["entry"].split("(")[0].split(",")[0].strip()
            card["definition"] = card["fields"]["Back"]["value"].split(
                "<br/>")[-1].split("<br>")[-1].split("(")[0].strip().strip("[]")

        return cards


    def load_dictionary(deck):
        d = Dictionary()
        decks = [key for key in Anki.list_decks().keys() if re.match(deck, key)]
        cards = []
        for deck in decks:
            ids = Anki.list_cards(deck)
            cards.extend(Anki.get_card_info(ids))

        reviewed = 0 #len([c for c in cards if c["reviewed"]])

        for card in cards:
            if card["reviewed"] or reviewed < 30:
                d.add(card["word"], card["definition"])

        return d, cards


