
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

        word = entry.split(",")[0].strip()
        self.entries[word] = {
            "word": word.strip(),
            "entry": entry.strip(),
            "definition": definition.strip(),
        }
        self.entries[entry.strip()] = self.entries[word]

        if form == "verb":
            self.verbs.add(word)
        elif form == "noun":
            self.nouns.add(word)
        else:
            self.other.add(word)
