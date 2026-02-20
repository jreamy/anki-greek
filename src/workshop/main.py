
import os, sys

dir_path = os.path.dirname(__file__)
libs_path = os.path.join(dir_path, "..", "libs")
if libs_path not in sys.path:
    sys.path.append(libs_path)

from dictionary import Dictionary

verbs = [
{ "entry": "εἰμί (pp1)", "definition": "I am" },
{ "entry": "ἀγαπάω (pp1)", "definition": "I love" },
{ "entry": "ἀγαπήσω (pp2)", "definition": "I will love" },
{ "entry": "ἤγαγον (pp3)", "definition": "I led, gathered" },
{ "entry": "ἀνέῳγα (pp4)", "definition": "I have opened" },
]
nouns = [
{ "entry": "τιμή, -ῆς, ἡ", "definition": "honor, price" },
{ "entry": "ζωή, ἡ", "definition": "life" },
{ "entry": "θάλασσα, ἡ", "definition": "sea, lake" },
{ "entry": "δόξα, ἡ", "definition": "glory, honor" },
{ "entry": "κύριος, ὁ", "definition": "Lord, master, owner" },
{ "entry": "νόμος, ὁ", "definition": "law" },
]

other = [
{ "entry": "ἀλλά", "definition": "but" },
{ "entry": "γάρ", "definition": "for" },
{ "entry": "δέ", "definition": "but, and" },
]

d = Dictionary()
for v in verbs:
    v["form"] = "verb"
    d.add(v)

for n in nouns:
    n["form"] = "noun"
    d.add(n)

for o in other:
    o["form"] = "other"
    d.add(o)


from generator import LLM
llm = LLM("Koine Greek", d, repo="ilsp/Llama-Krikri-8B-Instruct-GGUF", filename="*q4_k_m.gguf")

llm.get_verb_forms("ἀγαπήσω, (pp2)")
print(llm.generate("ἀγαπήσω", "ἀγαπήσω, (pp2)", "I will love"))

