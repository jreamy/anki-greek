

from aqt import mw
import re
from dictionary import Dictionary

def derive_fields(note, deck):

    fields = {}
    model = note.note_type()
    for fld in model['flds']:
        fields[fld['name']] = {
            "value": note[fld['name']],
            "order": fld['ord']
        }

    card_ids = [c.id for c in note.cards()]

    card = {
        "noteId": note.id,
        "cards": card_ids,
        "deck_id": deck["id"],
        "deck_conf": deck.get("conf"),
        "mod": note.mod,
        "modelName": model['name'],
        "tags": note.tags,
        "fields": fields
    }

    card["entry"] = card["fields"]["Front"]["value"].strip()
    card["word"] = card["entry"].split("(")[0].split(",")[0].strip()
    card["definition"] = card["fields"]["Back"]["value"].split("(")[0].strip().strip("[]")

    if "(+" in card["entry"]:
        card["form"] = "other"
    elif "," in card["entry"]:
        card["form"] = "noun"
    elif card["definition"].startswith("I ") or card["definition"].startswith("it is "):
        card["form"] = "verb"
    else:
        card["form"] = "other"

    return card

class Anki:

    def migrate_note(id: int):
        note = mw.col.get_note(id)
        target_model = mw.col.models.by_name("anki-greek")
        source_model = note.note_type()
        if source_model["name"] == "anki-greek" or not target_model:
            return
        print(f"anki-greek: migrating {id}")
        
        input = mw.col.models.change_notetype_info(
            old_notetype_id=source_model['id'],
            new_notetype_id=target_model['id']
        ).input
        input.note_ids.extend([id])
        
        mw.col.models.change_notetype_of_notes(input)
        mw.reset()


    def update_card(id: int, fields: dict = {}, tags: list = [], replace_tags: bool = False):
        Anki.migrate_note(id)

        # 1. Get the note object by its ID
        note = mw.col.get_note(id)
        for field_name, value in fields.items():
            if field_name in note:
                note[field_name] = value

        if replace_tags:
            note.tags = tags
        else:
            # Merge lists and remove duplicates
            note.tags = list(set(note.tags + tags))

        mw.col.update_note(note)
        mw.reset()
        return note

    def list_decks():
        decks_data = mw.col.decks.all_names_and_ids()
        return {d.name: d.id for d in decks_data}
    
    def list_cards(arg, query="deck"):
        return [int(x) for x in mw.col.find_notes(f"{query}:{arg}")]

    def list_tagged_cards(tag):
        return Anki.list_cards(tag, query="tag")

    def card_info(note_ids: list[int]):
        result = []
        for nid in note_ids:
            note = mw.col.get_note(nid)
            if not note:
                continue

            cards = note.card_ids()
            if len(cards) != 1:
                continue

            deck = mw.col.decks.get(mw.col.get_card(cards[0]).did)

            result.append(derive_fields(note, deck))

        return result

    def get_reviews(card_ids: list[int]):
        result = {}
        for cid in card_ids:
            # Fetch all review logs for this specific card ID
            # Returns a list of: [id, cid, usn, ease, ivl, last_ivl, factor, time, type]
            reviews = mw.col.db.all(
                "select id, ease, ivl, lastIvl, factor, time, type from revlog where cid = ?",
                cid
            )

            card_reviews = []
            for rev in reviews:
                card_reviews.append({
                    "id": rev[0],        # Review timestamp (ms)
                    "ease": rev[1],      # Which button was pressed (1-4)
                    "ivl": rev[2],       # New interval
                    "lastIvl": rev[3],   # Previous interval
                    "factor": rev[4],    # New ease factor
                    "time": rev[5],      # Time taken to review (ms)
                    "type": rev[6]       # 0=learn, 1=review, 2=relearn, 3=cram
                })
            result[str(cid)] = card_reviews
        return result

    def get_card_info(ids):
        cards = Anki.card_info(ids)
        reviews = Anki.get_reviews(
            [c for card in cards for c in card["cards"]])

        for card in cards:
            revs = [r for c in card["cards"] for r in reviews[str(c)]]
            card["reviewed"] = int(max([int(x["id"])
                                        for x in revs]) / 1000) if len(revs) else 0

        return cards
    
    def get_review_config(conf_id):
        cfg = mw.col.decks.get_config(conf_id)
        return {
            "id": conf_id,
            "enabled": cfg.get("anki_greek_enabled", False),
            "dialect": cfg.get("anki_greek_dialect", "Koine Greek"),
            "model": {
                "repo": cfg.get("anki_greek_model_repo", ""),
                "filename": cfg.get("anki_greek_model_filename", ""),
            },
            "verb_moods": cfg.get("anki_greek_verb_moods", ""),
        }
    
    def list_decks_by_config(cfg_id):
        """
        Returns a dictionary mapping Config ID -> List of Deck IDs.
        Example: {1: [164210, 164211], 1770481: [164215]}
        """
        decks = []
        
        # mw.col.decks.all_names_and_ids() returns a list of DeckIdAndName objects
        for deck_id_name in mw.col.decks.all_names_and_ids():
            did = deck_id_name.id
            deck = mw.col.decks.get(did)
            
            if deck.get("conf") == cfg_id:
                decks.append(deck)
                
        return decks


    def load_dictionary(decks: list[str], review_min_threshold=30):
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
    
    def load_dict(decks: list[int], review_min_threshold=30):
        d = Dictionary()
        cards = []
        for deck in decks:
            ids = Anki.list_cards(deck)
            cards.extend(Anki.get_card_info(ids))

        reviewed = len([c for c in cards if c["reviewed"]])

        for card in cards:
            if card["reviewed"] or reviewed < review_min_threshold:
                d.add(card)

        return d

    def get_or_create_custom_model():
        model_name = "anki-greek"
        mm = mw.col.models
        
        # 1. Check if it already exists
        existing = mm.by_name(model_name)
        if existing:
            return existing

        # 2. Create the base model
        model = mm.new(model_name)
        
        # 3. Add Fields
        for field_name in ["Front", "Back", "Story", "Translation"]:
            fld = mm.new_field(field_name)
            mm.add_field(model, fld)

        # 4. Add the Template
        template = mm.new_template("Standard Card")
        template['qfmt'] = "<div style='color:var(--link)'>{{Story}}</div><div style='font-size:small'>[{{Front}}]</div>"
        template['afmt'] = "{{FrontSide}}<hr id=answer><div style='color:var(--graded-good)'>{{Translation}}</div><div style='font-size:small'>[{{Back}}]</div>"
        mm.add_template(model, template)

        # 5. Add custom CSS (Optional but recommended)
        model['css'] += "\n.card { text-align: center; font-size: 20px; }\n"

        # 6. Save to collection
        mm.add(model)
        return model
    