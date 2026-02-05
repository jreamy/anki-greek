import sys
from llm import LLM
from anki import Anki
import json

with open(sys.argv[1]) as f:
    cfg = json.load(f)


if __name__ == "__main__":
    Anki.sync()

    dictionary, cards = Anki.load_dictionary(cfg["decks"])
    for form in cfg["forms"]:
        dictionary.forms.add(form)

    llm = LLM(cfg["model"]["repo"], cfg["model"]["file"],
              cfg["output"]["dialect"], dictionary)

    try:
        for card in cards:
            if "generated" in card["tags"] and card["mod"] > card["reviewed"]:
                continue

            print("updating", card["word"], "-",
                  card["definition"], f"({card["form"]})")

            front, back = llm.generate(
                card["word"], card["entry"], card["definition"], length=cfg["output"]["length"], dict_limit=20)
            Anki.update_card(card["noteId"], {
                "Front": f"{front}<br/>[{card["entry"]}]",
                "Back": f"{back}<br/>[{card["definition"]}]",
            })

            Anki.add_tags([card["noteId"]], "generated")

    except KeyboardInterrupt:
        pass

    finally:
        llm.close()
        Anki.sync()
