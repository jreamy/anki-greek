
from llama_cpp import Llama
import random
import re
import time

import os
import sys
from contextlib import contextmanager

default_verb_moods = ["indicative", "imperative", "infinitive", "participle"]


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


class LLM:
    def __init__(self, dialect: str, dictionary, verb_moods: list[str] = default_verb_moods, repo="", filename="", **kwargs: dict):

        with silence_stderr():
            self.llm = Llama.from_pretrained(
                repo, filename,
                n_gpu_layers=-1,
                verbose=False,
                n_ctx=1024,
                **kwargs,
            )

        self.dialect = dialect
        self.dictionary = dictionary
        self.verb_moods = verb_moods

    def close(self):
        self.llm.close()

    def generate(self, word, entry, definition, desc="phrase", max_tokens=128, dict_limit=None):
        seed = int(round(time.time() * 1000))

        self.llm.reset()

        verbs = self.dictionary.verbs if not dict_limit else random.sample(
            list(self.dictionary.verbs), min(len(self.dictionary.verbs), dict_limit))
        nouns = self.dictionary.nouns if not dict_limit else random.sample(
            list(self.dictionary.nouns), min(len(self.dictionary.nouns), dict_limit))
        other = self.dictionary.other if not dict_limit else random.sample(
            list(self.dictionary.other), min(len(self.dictionary.other), dict_limit))

        if word in self.dictionary.verbs:
            verb, v_entry = word, entry
        else:
            verb = random.choice(list(self.dictionary.verbs))
            v_entry = self.dictionary.entries[verb]["entry"]

        verb_form = random.choice(self.get_verb_forms(v_entry))
        verb_mood = random.choice(self.verb_moods)

        if word in self.dictionary.nouns:
            noun, n_entry = word, entry
        else:
            noun = random.choice(list(self.dictionary.nouns))
            n_entry = self.dictionary.entries[noun]["entry"]
        
        # Map person to appropriate noun cases
        person_to_cases = {
            "first": ["accusative", "dative", "genitive"],
            "second": ["vocative", "accusative", "dative", "genitive"],
            "third": ["nominative", "accusative", "dative", "genitive"]
        }
        
        person = random.choice(["first", "second", "third"])
        allowed_cases = person_to_cases[person]
        number = random.choice(["singular", "plural"])
        noun_form = f"{random.choice(allowed_cases)} {number}"

        if verb_mood == "imperative":
            verb_form += f" {verb_mood} second person {number}"
            noun_form = f"vocative {number}"
        elif verb_mood == "infinitive":
            verb_form += f" {verb_mood}"
            noun_form = f"accusitive {number}"
        elif verb_mood == "participle":
            number = random.choice(["singular", "plural"])
            verb_form += f" {noun_form} {verb_mood}"
        else:
            verb_form += f" {verb_mood} {person} person {number}"

        verb = self.conjugate(verb, verb_form, seed=seed)

        if word in self.dictionary.other:
            phrase = word
            cases = self.get_cases(entry)
            if len(cases) == 1:
                phrase = f"{word} {self.decline(n_entry, cases[0], seed=seed)}"
        else:
            phrase = self.decline(n_entry, noun_form, seed=seed)

        output = self.llm.create_chat_completion([
            {
                "role": "system",
                "content": f"You are a helpful assistant. If the user prompts in English, respond in {self.dialect}. After generating a response, double check it meets all the contraints provided by the user",
            },
            {
                "role": "user",
                "content": f"""
Allowed Verbs: {", ".join(verbs)}
Allowed Nouns: {", ".join(nouns)}
Other Allowed Words: {", ".join(other)}
Task: Use the above words to generate a short {desc} in {self.dialect} demonstrating the use of {phrase} and {verb}.
Constraints: 
 - Include only allowed nouns, verbs, or other words provided above.
 - Include no explanation or preamble.
 - Include only {self.dialect} word forms, no other dialect, not Modern Greek.
 - Correct all verb forms to agree with their subject.
 - Correct all agreement, spelling, and accents according to {self.dialect}.
 - The {desc} should be short and grammatically correct.
 - The {desc} must focus on the {noun_form} {"phrase" if " " in phrase else "word"} '{phrase}'.
 - The {desc} must focus on the {verb_form} verb '{verb}'.
"""},
        ], max_tokens=max_tokens, seed=seed)

        story = output['choices'][0]["message"]['content'].strip()
        story = story.split("(Note")[0].split("(Translat")[0].strip()

        return story, self.translate(story, word, definition, desc=desc, max_tokens=max_tokens, seed=seed)

    def translate(self, story, word, definition, desc="phrase", max_tokens=128, seed=None):
        output = self.llm.create_chat_completion([
            {
                "role": "system",
                "content": "You are a helpful assistant. You respond only to the task at hand and include no extra dialogue.",
            }, {
                "role": "user",
                "content": f"""
Task: Translate the following {self.dialect} {desc} into english.
Constraints:
 - Prefer a word-for-word translation when possible.
 - Include only the translation in the output.
 - Do not include content that is not in the original {desc}.
 - Correct any agreement issues or incorrect spelling.
 - Use {self.dialect} definitions when translating.
 - Use the {self.dialect} definition of {word}: {definition}.

Original: {story}
"""},
        ], max_tokens=max_tokens, seed=seed)

        story = output['choices'][0]["message"]['content'].strip()
        story = story.split("(Note")[0].split("(Translat")[0].strip()

        return story

    def conjugate(self, word, form, seed=None):
        self.llm.reset()

        negation = "active"
        if "active" in form:
            negation = "passive or middle"

        output = self.llm.create_chat_completion([
            {
                "role": "system",
                "content": f"You are a helpful assistant, very adept at writing in {self.dialect}. After generating a response, double check it meets all the contraints provided by the user. Your response is one word.",
            },
            {
                "role": "user",
                "content": f"""
Task: provide the {form} of '{word}' in {self.dialect}. 
Constraints:
 - Use {self.dialect} conjugation rules not Modern Greek.
 - Use {form} endings, not {negation} endings.
 - Your response must be a form of '{word}'.
"""},
        ], max_tokens=32, seed=seed)

        return output['choices'][0]["message"]['content'].strip().lower()

    def decline(self, word, form, seed=None):
        output = self.llm.create_chat_completion([
            {
                "role": "system",
                "content": f"You are a helpful assistant, very adept at writing in {self.dialect}. Your response is two words.",
            },
            {
                "role": "user",
                "content": f"""
Task: provide the {form} of {word} in {self.dialect}. Include the article in the output.
"""},
        ], max_tokens=32, seed=seed)

        output = output['choices'][0]["message"]['content'].strip().lower()
        if len(output.split(" ")) > 2:
            output = " ".join(output.split(" ")[0:2])

        return output

    def get_cases(self, entry):
        cases = {
            "nom": "nominative",
            "gen": "genitive",
            "acc": "accusative",
            "dat": "dative",
            "voc": "vocative",
        }

        return [cases[x] for x in re.findall(r"\(\+?\s?(dat|gen|acc|voc|nom)\.?\)", entry)]

    def get_verb_forms(self, entry):

        principle_parts = {
            "1": ["present active", "present middle", "present passive", "imperfect active", "imperfect middle", "imperfect passive"],
            "2": ["future active", "future middle"],
            "3": ["aorist active", "aorist middle"],
            "4": ["perfect active", "pluperfect active"],
            "5": ["perfect middle", "perfect passive", "pluperfect middle", "pluperfect passive"],
            "6": ["aorist passive", "future passive"],
        }

        pps = re.findall(r"\(pp(\d)\)", entry)
        if len(pps) == 0:
            return principle_parts["1"]
        elif len(pps) == 1:
            return principle_parts[pps[0]]
        else:
            return list(set([pp for x in pps for pp in principle_parts[x]]))
