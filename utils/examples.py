import csv
import re
from typing import List

import ollama
import config


def _normalize_language_code(language_code: str) -> str:
    if not language_code:
        return ""
    return language_code.strip().lower()


def _word_in_sentence(word: str, sentence: str) -> bool:
    if not word or not sentence:
        return False
    pattern = r"(?i)\b" + re.escape(word) + r"\b"
    return re.search(pattern, sentence) is not None


def get_tatoeba_examples(word: str, language_code: str, limit: int = 5) -> List[str]:
    """
    Returns up to `limit` example sentences from the local Tatoeba `data/sentences.csv`
    that contain the `word` and match `language_code`.

    The CSV format is expected to be: id\tlanguage\tsentence
    """
    language_code = _normalize_language_code(language_code)

    results: List[str] = []
    try:
        with open(r"C:\Users\DNS_PC\PycharmProjects\ForWordsBot\data\sentences.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) < 3:
                    continue
                lang = _normalize_language_code(row[1])
                sentence = row[2]
                if language_code and lang != language_code:
                    continue
                if _word_in_sentence(word, sentence):
                    results.append(sentence)
                    if len(results) >= limit:
                        break
    except Exception:
        return []

    return results


async def generate_examples_with_ollama(word: str, language_code: str, limit: int = 5) -> List[str]:
    url = getattr(config, "OLLAMA_URL", 'localhost:11434')
    model = getattr(config, "OLLAMA_MODEL", "llama3.1:8b")

    prompt = (
        "You generate short, natural example sentences for language learners. "
        "Keep each sentence under 15 words. Return plain sentences, no numbering.\n"
        f"Create {limit} example sentences in {language_code} using the word '{word}'.\n"
        f"Use different contexts and common collocations."
    )

    client = ollama.AsyncClient()

    decision = await client.generate(model, f"Can you provide some sentences in language {language_code}? "
                                            f"Your answer should be 'True' or 'False'.",
                                     system="You are a format-strict assistant. "
                                            "Always answer with exactly one token: either True or False. "
                                            "Do not add punctuation, explanation, or whitespace. "
                                            "If you cannot answer, return False.",
                                     options={"temperature": 0.0})

    if decision.get("response") == 'False':
        print("Sorry, but our model doesn't know this language.")
        return []
    else:
        response = await client.generate(model, prompt)
        sentences = response.get("response").replace("\n\n", "\n").split("\n")
        return sentences


async def get_examples(word: str, language_code: str, limit: int = 5, llm: bool = False) -> List[str]:
    if llm:
        return await generate_examples_with_ollama(word=word, language_code=language_code, limit=limit)
    else:
        results = get_tatoeba_examples(word=word, language_code=language_code, limit=limit)
        if len(results) < limit:
            need = limit - len(results)
            results += await generate_examples_with_ollama(word=word, language_code=language_code, limit=need)
        return results
