
import requests
import re
from dictionary import Dictionary

# docs: https://git.sr.ht/~foosoft/anki-connect


class Anki:

    def create_card(front, back, deck):
        return requests.post("http://localhost:8765", json={
            "action": "addNotes",
            "version": 6,
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
    
    def update_card(id, fields, tags=[]):
        card = requests.post("http://localhost:8765", json={
            "action": "updateNoteFields",
            "version": 6,
            "params": {
                "note": {
                    "id": id,
                    "fields": fields,
                }
            }
        }).json()["result"]
        for tag in tags:
            Anki.add_tags([id], tag)

        return card

    def tagged_cards():
        return requests.post("http://localhost:8765", json={
            "action": "findNotes",
            "version": 6,
            "params": {
                "query": "tag:generated"
            }
        }).json()["result"]

    def list_cards(deck):
        return requests.post("http://localhost:8765", json={
            "action": "findNotes",
            "version": 6,
            "params": {
                "query": f"deck:{deck}"
            }
        }).json()["result"]

    def card_info(ids):
        return requests.post("http://localhost:8765", json={
            "action": "notesInfo",
            "version": 6,
            "params": {
                "notes": ids
            }
        }).json()["result"]



    def get_reviews(ids):
        return requests.post("http://localhost:8765", json={
            "action": "getReviewsOfCards",
            "version": 6,
            "params": {
                "cards": ids,
            }
        }).json()["result"]

    def add_tags(ids, tags):
        return requests.post("http://localhost:8765", json={
            "action": "addTags",
            "version": 6,
            "params": {
                "notes": ids,
                "tags": tags,
            }
        }).json()

    def list_decks():
        return requests.post("http://localhost:8765", json={
            "action": "deckNamesAndIds",
            "version": 6,
        }).json()["result"]

    def sync():
        return requests.post("http://localhost:8765", json={
            "action": "sync",
            "version": 6,
        }).json()["result"]

    def get_card_info(ids):
        cards = Anki.card_info(ids)
        reviews = Anki.get_reviews(
            [c for card in cards for c in card["cards"]])

        for card in cards:
            revs = [r for c in card["cards"] for r in reviews[str(c)]]
            card["reviewed"] = int(max([int(x["id"])
                                        for x in revs]) / 1000) if len(revs) else 0

            card["entry"] = card["fields"]["Front"]["value"].split(
                "<br/>")[-1].split("<br>")[-1].strip().strip("[]")
            card["word"] = card["entry"].split("(")[0].split(",")[0].strip()
            card["definition"] = card["fields"]["Back"]["value"].split(
                "<br/>")[-1].split("<br>")[-1].split("(")[0].strip().strip("[]")
            
            if "(+" in card["entry"]:
                card["form"] = "other"
            elif "," in card["entry"]:
                card["form"] = "noun"
            elif card["definition"].startswith("I ") or card["definition"].startswith("it is "):
                card["form"] = "verb"
            else:
                card["form"] = "other"

        return cards

    def load_dictionary(decks: list[str], review_min_threshold = 30):
        d = Dictionary()
        decks = [key for key in Anki.list_decks().keys() if any(
            [re.match(deck+"$", key) for deck in decks])]
        cards = []
        for deck in decks:
            ids = Anki.list_cards(deck)
            cards.extend(Anki.get_card_info(ids))

        reviewed = len([c for c in cards if c["reviewed"]])

        for card in cards:
            if card["reviewed"] or reviewed < review_min_threshold:
                d.add(card)

        return d, cards
