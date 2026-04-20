
import unicodedata

class Dictionary():

    def __init__(self):
        self.verbs = set()
        self.nouns = set()
        self.other = set()
        self.forms = set()
        self.entries = dict()

    def add(self, card):

        entry = card["entry"]
        definition = card["definition"]
        form = card["form"]

        ending = ''.join([x for x in unicodedata.normalize('NFD', entry.split(" ")[-1]) if "GREEK" in unicodedata.name(x, '')])
        if ending == ("η"):
            gender = "feminine"
        elif ending == "ο":
            gender = "masculine"
        elif ending == "το":
            gender = "neuter"
        else:
            gender = None

        word = entry.split(",")[0].split("(")[0].strip()
        self.entries[word] = {
            "word": word.strip(),
            "entry": entry.strip(),
            "definition": definition.strip(),
            "gender": gender,
        }
        self.entries[entry.strip()] = self.entries[word]


        if form == "verb":
            self.verbs.add(word)
        elif form == "noun":
            self.nouns.add(word)
        else:
            self.other.add(word)
