
from llama_cpp import Llama
from .dictionary import Dictionary
import random
import re
import time


class LLM:
    def __init__(self, dialect: str, dictionary: Dictionary, repo = "", filename = "", **kwargs: dict):

        self.llm = Llama.from_pretrained(
            repo, filename,
            n_gpu_layers=-1,
            verbose=False,
            n_ctx=1024,
            **kwargs,
        )

        self.dialect = dialect
        self.dictionary = dictionary

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

        verb_form = random.choice(list(self.dictionary.forms)) if len(
            self.dictionary.forms) else "present active indicative"

        if "imperative" in verb_form:
            verb_form = f"second person {random.choice(["singular", "plural"])}"
        elif "infinitive" not in verb_form:
            verb_form = f"{random.choice(["first", "second", "third"])} person {random.choice(["singular", "plural"])}"

        noun_form = random.choice(
            ["nominative", "accusative", "genitive", "dative", "vocative"])

        if word in self.dictionary.verbs:
            word = self.conjugate(word, verb_form, seed=seed)
        elif word in self.dictionary.nouns:
            word = self.conjugate(word, noun_form, seed=seed)

        cases = self.get_cases(entry)
        phrase = word
        if len(cases) == 1:
            phrase = f"{word} {self.decline(random.sample(list(self.dictionary.nouns), 1)[0], cases[0])}"

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
Task: Use the above words to generate a short {desc} in {self.dialect} demonstrating the use of {phrase}.
Constraints: 
 - Include only allowed nouns, verbs, or other words provided above.
 - Include no explanation or preamble.
 - Include only {self.dialect} word forms, no other dialect, not Modern Greek.
 - Correct all verb forms to agree with their subject.
 - Correct all agreement, spelling, and accents according to {self.dialect}.
 - Use {verb_form} at least once.
 - The {desc} should be short and grammatically correct.
 - The {desc} must focus on the {"phrase" if " " in phrase else "word"} '{phrase}'.
"""},
        ], max_tokens=max_tokens, seed=seed)

        story = output['choices'][0]["message"]['content'].strip()

        return story, self.translate(story, word, definition, desc=desc, max_tokens=max_tokens, seed=seed)

    def translate(self, story, word, definition, desc="phrase", max_tokens=128, seed=None):
        output = self.llm.create_chat_completion([
            {
                "role": "system",
                "content": "You are a helpful assistant. You respond only to the task at hand and include no extra dialogue.",
            }, {
                "role": "user",
                "content": f"""
Task: Translate the following {desc} into english.
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

        return output['choices'][0]["message"]['content'].strip()

    def conjugate(self, word, form, seed=None):
        output = self.llm.create_chat_completion([
            {
                "role": "system",
                "content": f"You are a helpful assistant, very adept at writing in {self.dialect}. Your response is one word.",
            },
            {
                "role": "user",
                "content": f"""
Task: provide the {form} of {word} in {self.dialect}. Do not include articles in the output.
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
