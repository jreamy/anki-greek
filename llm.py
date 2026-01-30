
from llama_cpp import Llama
from dictionary import Dictionary
import random
import time


class LLM:
    def __init__(self, repo: str, file: str, dialect: str, dictionary: Dictionary):

        self.llm = Llama.from_pretrained(
            repo_id=repo,
            filename=file,
            n_gpu_layers=-1,
            verbose=False,
            n_ctx=1024,
        )

        self.dialect = dialect
        self.dictionary = dictionary

    def close(self):
        self.llm.close()

    def generate(self, word, length=3, dict_limit=None):
        seed = int(round(time.time() * 1000))

        self.llm.reset()

        verbs = self.dictionary.verbs if not dict_limit else random.sample(
            list(self.dictionary.verbs), min(len(self.dictionary.verbs), dict_limit))
        nouns = self.dictionary.nouns if not dict_limit else random.sample(
            list(self.dictionary.nouns), min(len(self.dictionary.nouns), dict_limit))
        other = self.dictionary.other if not dict_limit else random.sample(
            list(self.dictionary.other), min(len(self.dictionary.other), dict_limit))

        form = random.choice(list(self.dictionary.forms)) if len(self.dictionary.forms) else "present tense"

        length_rule, desc = (f"""
 - The story should be {length} sentences long.
 - Include complete sentences.
 - The story should use multiple forms of {word} if possible.
        """, "story") if length > 1 else ("""
 - The output should be 1 brief sentence.
        """, "sentence") if length == 1 else ("""
 - The output should be a short phrase.
        """, "phrase")

        form_promt = f"The {desc} should use '{word}' in the {form}" if word in self.dictionary.verbs else f"The {desc} should use a verb in the {form}"


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
Task: Use the above words to generate a short {desc} in {self.dialect} demonstrating the use of {word}.
Constraints: 
 - Include only allowed nouns, verbs, or other words provided above.
 - Include no explanation or preamble.
 - Include only {self.dialect} word forms, no other dialect, not Modern Greek.
 - Correct all verb forms to agree with their subject.
 - Correct all agreement, spelling, and accents according to {self.dialect}.
 {length_rule.strip()}
 - Primarily use {random.choice(["first", "second", "third"])} person {random.choice(["singular", "plural"])}.
 - {form_promt}.
 - The {desc} should focus on the word '{word}'.
"""},
        ], max_tokens=length * 256, seed=seed)

        # .split('\n')[0]
        story = output['choices'][0]["message"]['content'].strip()

        output = self.llm.create_chat_completion([
            {
                "role": "system",
                "content": f"You are a helpful assistant, very adept at writing in {self.dialect}. You respond only to the task at hand and include no extra dialogue.",
            },
            {
                "role": "user",
                "content": f"""
Task: correct the following {desc} so it contains only correct {self.dialect}.
Constraints: 
 - Include no explanation or preamble.
 - Include only the corrected form in the output.
 - Correct all verb forms to agree with their subject.
 - Correct all agreement, spelling, and accents according to {self.dialect}.
 - Include only {self.dialect}.
 - Replace any Modern Greek with {self.dialect}.

Original: '{story}'
"""},
        ], max_tokens=length * 256, seed=seed)

        story = output['choices'][0]["message"]['content'].strip()

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

Original: {story}
"""},
        ], max_tokens=length * 256, seed=seed)

        translation = output['choices'][0]["message"]['content'].strip()

        return story, translation
