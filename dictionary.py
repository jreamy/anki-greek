
class Dictionary():

    def __init__(self):
        self.verbs = set()
        self.nouns = set()
        self.other = set()
        self.forms = set()
        self.entries = dict()

    def add(self, entry, definition):

        word = entry.split(",")[0].strip()
        self.entries[word] = {
            "word": word.strip(),
            "entry": entry.strip(),
            "definition": definition.strip(),
        }
        self.entries[entry.strip()] = self.entries[word]

        if "(+" in entry:
            self.other.add(word)
        elif "," in entry:
            self.nouns.add(word)
        elif definition.startswith("I ") or definition.startswith("it is "):
            self.verbs.add(word)
        else:
            self.other.add(word)
