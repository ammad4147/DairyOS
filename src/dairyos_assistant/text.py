"""Operator-language normalisation: tokens, stemming, synonyms and spelling.

Operators type short, misspelled, mixed-language questions ("cow fresh 2 days
not eating", "bachre ko dast", "withdrawl days"). Retrieval should not depend on
developer vocabulary, so every query and every knowledge record pass through
the same normaliser:

1. lower-case, strip punctuation, split into tokens;
2. expand known operator shorthand and Roman-Urdu farm words into their
   English terms (expansion, never replacement, so an exact match still counts);
3. correct unknown words against the knowledge vocabulary within a small edit
   distance;
4. reduce each token to a light stem so "calves"/"calf", "calving"/"calved"
   and "inseminations"/"insemination" meet.

Standard library only. Deterministic: the same text always gives the same
tokens, which keeps retrieval explainable and testable.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field

_WORD = re.compile(r"[a-z0-9]+(?:[/'][a-z0-9]+)?")

STOPWORDS = frozenset(
    """a about an and are as at be by can could did do does doing for from get got had has have how i if in into is it
    its me my of on or our please should so than that the their them then there these they this those to too us was we
    were what when where which who whom why will with would you your yours ko ki ka ke hai hain kya kaise kese kab kahan
    mein me se aur ya bhi karein karun kar krna krne karna karte hota hoti hoty tha thi dein dun wo ye yeh just also
    tell show explain give let any some more much many very help tips please ok okay""".split()
)

# Phrase-level expansions: operator shorthand, Roman-Urdu and synonyms. Each
# key is matched on word boundaries in the lower-cased text; the value's words
# are appended to the token stream.
PHRASES: dict[str, str] = {
    # DairyOS vocabulary
    "cop": "cost production per litre coml",
    "coml": "cost production per litre cop",
    "cost of milk": "cost production cop",
    "cost per litre": "cost production cop",
    "cost per liter": "cost production cop",
    "kharcha": "cost expense",
    "opex": "operating expense opex",
    "capex": "capital non-opex equipment",
    "tmr": "tmr total mixed ration feed",
    "ration": "ration tmr feed",
    "wanda": "vanda concentrate feed",
    "vanda": "concentrate feed vanda",
    "bhoosa": "wheat straw feed",
    "khal": "cake protein feed",
    "khal banola": "cottonseed cake feed",
    "choker": "wheat bran feed",
    "chara": "fodder feed",
    "pd": "pregnancy diagnosis pd",
    "p.d": "pregnancy diagnosis pd",
    "pregnancy check": "pregnancy diagnosis pd",
    "preg check": "pregnancy diagnosis pd",
    "ai": "artificial insemination ai",
    "a.i": "artificial insemination ai",
    "ai man": "inseminator technician insemination",
    "semen": "semen straw",
    "straw": "semen straw",
    "straws": "semen straw",
    "vwp": "voluntary waiting period",
    "dim": "days in milk",
    "scc": "somatic cell count scc",
    "cmt": "california mastitis test",
    "snf": "solids not fat snf quality",
    "bcs": "body condition score bcs",
    "thi": "temperature humidity index heat stress",
    "void": "void cancel",
    "delete": "void delete remove",
    "cancel": "void cancel",
    "passport": "passport animal history",
    "udhaar": "credit payable receivable",
    "udhar": "credit payable receivable",
    "tankhwah": "salary payroll wages",
    "salary": "salary payroll wages",
    "wages": "wages payroll salary",
    "dodhi": "milk buyer sale",
    "report": "report reporting",
    "repot": "report reporting",
    "bakup": "backup",
    "back up": "backup",
    "settings": "settings",
    # Animals and life stages (English variants)
    "freshened": "calved fresh cow calving",
    "fresh cow": "fresh cow calved calving after",
    "cow fresh": "fresh cow calved calving after",
    "calved": "calved calving",
    "delivery": "calving calved birth",
    "byai": "calving calved",
    "close up": "close-up closeup",
    "close-up": "close-up closeup",
    "closeup": "close-up closeup",
    "clsoe up": "close-up closeup",
    "far off": "far-off",
    "dry off": "dry-off dry",
    "drying off": "dry-off dry",
    "downer": "down cow recumbent",
    "down cow": "down cow recumbent",
    "cannot stand": "down cow recumbent",
    "cannot get up": "down cow recumbent",
    "can't get up": "down cow recumbent",
    "afterbirth": "placenta afterbirth",
    "jer": "placenta afterbirth",
    # Roman-Urdu farm words
    "gai": "cow", "gaye": "cow", "gaey": "cow", "gaaye": "cow",
    "bhains": "buffalo", "bhens": "buffalo", "bhains ": "buffalo",
    "bachra": "calf", "bachre": "calf", "bachri": "calf", "bachhra": "calf", "katta": "calf", "katti": "calf", "bacha": "calf fetus",
    "janwar": "animal", "maweshi": "animal livestock",
    "doodh": "milk", "dudh": "milk",
    "bohli": "colostrum", "boli": "colostrum", "khees": "colostrum",
    "dast": "diarrhea scours", "pechis": "diarrhea dysentery",
    "loose motion": "diarrhea scours", "loose motions": "diarrhea scours", "loose dung": "diarrhea loose manure",
    "watery dung": "diarrhea scours", "patla gobar": "diarrhea scours",
    "bukhar": "fever temperature", "bukhaar": "fever temperature",
    "khansi": "cough", "zukam": "nasal discharge",
    "thun": "udder teat", "thanela": "mastitis",
    "garam": "heat", "garmi": "heat stress hot weather", "hanp": "panting", "haanp": "panting",
    "afara": "bloat", "aphara": "bloat",
    "langra": "lame lameness", "langra pan": "lameness lame",
    "tika": "vaccine vaccination", "teeka": "vaccine vaccination",
    "keeray": "worms parasites", "kide": "worms parasites",
    "mooh khur": "foot mouth disease fmd", "munh khur": "foot mouth disease fmd",
    "galghotu": "haemorrhagic septicaemia hs", "gal ghotu": "haemorrhagic septicaemia hs",
    "paani": "water", "pani": "water",
    "mandi": "market purchased animal",
    "naal": "navel",
    "sust": "dull lethargic",
    "bimar": "sick", "beemar": "sick", "bimari": "disease sick",
    "mar gayi": "died dead deceased", "mar gaya": "died dead deceased",
    "gir gaya": "abortion loss", "bacha gir": "abortion pregnancy loss",
    "aaj": "today",
    "light gone": "power outage not milked session", "bijli": "power outage electricity",
    "power cut": "power outage not milked", "load shedding": "power outage not milked",
    "no electricity": "power outage not milked", "power failed": "power outage not milked",
    "stop milk to calf": "weaning wean", "stop milk feeding": "weaning wean", "stop giving milk": "weaning wean",
    "milking cows": "milking category herd count", "milking list": "milking lactating return",
    "entry": "record enter entry", "entery": "record enter entry", "likhun": "record enter",
    "2 times": "twice daily", "two times": "twice daily", "do waqt": "twice daily", "do dafa": "twice daily",
    "3 times": "thrice daily", "three times": "thrice daily", "teen waqt": "thrice daily", "teen dafa": "thrice daily",
    # English symptom synonyms
    "diarrhea": "diarrhea scours", "diarrhoea": "diarrhea scours", "scours": "scours diarrhea",
    "not eating": "off feed appetite not eating", "off feed": "off feed appetite not eating",
    "eating poorly": "appetite off feed", "eating less": "appetite intake off feed",
    "stopped eating": "off feed appetite not eating", "not eating much": "appetite off feed",
    "breathing fast": "breathing respiratory pneumonia", "coughing": "cough respiratory",
    "nose running": "nasal discharge", "runny nose": "nasal discharge",
    "limping": "lame lameness", "lame": "lameness",
    "temperature high": "fever temperature", "high temperature": "fever temperature",
    "temperature": "temperature fever",
    "clots": "clots mastitis abnormal milk", "flakes": "flakes mastitis abnormal milk",
    "swollen udder": "udder swelling mastitis", "hard quarter": "udder swelling mastitis",
    "heat detection": "heat signs estrus",
    "in heat": "heat signs estrus", "on heat": "heat signs estrus",
    "coming in heat": "heat signs estrus",
    "abortion": "abortion pregnancy loss", "aborted": "abortion pregnancy loss", "miscarriage": "abortion pregnancy loss",
    "antibiotic": "antibiotic medicine drug", "injection": "injection medicine drug",
    "dose": "dose dosage medicine", "dosage": "dose dosage medicine",
    "deworm": "deworm parasites worms", "dewormer": "deworm parasites worms",
}

# Word-level canonicalisation applied after tokenising (before stemming).
WORDS: dict[str, str] = {
    "litres": "litre", "liters": "litre", "liter": "litre", "ltr": "litre", "ltrs": "litre",
    "cows": "cow", "calves": "calf", "heifers": "heifer", "buffaloes": "buffalo",
    "vaccine": "vaccination", "vaccines": "vaccination", "vaccinate": "vaccination", "vaccinations": "vaccination",
    "inseminate": "insemination", "inseminated": "insemination",
    "pregnant": "pregnancy", "preg": "pregnancy",
    "withdrawl": "withdrawal", "withdrawals": "withdrawal",
    "colostrums": "colostrum",
    "mastitus": "mastitis",
    "expence": "expense", "expences": "expense",
    "seman": "semen",
    "vacination": "vaccination",
    "equipmant": "equipment",
    "purchse": "purchase",
    "yeild": "yield",
    "diarhea": "diarrhea", "diarrohea": "diarrhea",
    "calclated": "calculated", "calclate": "calculate",
    "pregnency": "pregnancy", "diagnsis": "diagnosis",
    "entery": "entry", "recrod": "record",
    "preperation": "preparation",
    "fmd": "fmd", "lsd": "lsd",
}

_SUFFIXES = (
    ("ational", "ate"), ("ization", "ize"), ("fulness", "ful"), ("ousness", "ous"),
    ("iveness", "ive"), ("ments", "ment"), ("ings", ""), ("ing", ""), ("edly", ""),
    ("ies", "y"), ("ied", "y"), ("ed", ""), ("es", ""), ("s", ""),
)
_KEEP = frozenset(
    "cows is was has this his gas bus plus less loss mass pass process stress grass mastitis ketosis brucellosis"
    " tuberculosis diagnosis prognosis septicaemia parasites scours bvd ibr fmd lsd hs snf scc tmr opex cop coml"
    " yes series species analysis abomasum ration dairyos vs status news".split()
)


def stem(token: str) -> str:
    """A deliberately light stemmer: enough to unify plurals and tenses."""
    if token in _KEEP or len(token) <= 3 or token.isdigit():
        return token
    for suffix, replacement in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            base = token[: len(token) - len(suffix)] + replacement
            if suffix in {"ing", "ed"} and len(base) > 2 and base[-1] == base[-2] and base[-1] not in "lsz":
                base = base[:-1]  # stopped -> stop, planned -> plan
            return base
    return token


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().replace("’", "'")


def raw_tokens(text: str) -> list[str]:
    tokens = []
    for token in _WORD.findall(_fold(text)):
        token = token.replace("'", "")
        tokens.extend(part for part in token.split("/") if part)
    return tokens


def _phrase_expansions(folded: str) -> list[str]:
    extra: list[str] = []
    padded = f" {' '.join(_WORD.findall(folded))} "
    for phrase, expansion in PHRASES.items():
        if f" {phrase} " in padded:
            extra.extend(expansion.split())
    return extra


def _phrase_expansions_with_keys(folded: str) -> list[tuple[str, list[str]]]:
    found = []
    padded = f" {' '.join(_WORD.findall(folded))} "
    for phrase, expansion in PHRASES.items():
        if f" {phrase} " in padded:
            found.append((phrase, expansion.split()))
    return found


def edit_distance_at_most(a: str, b: str, limit: int) -> int | None:
    """Levenshtein distance with early exit; None when over ``limit``."""
    if abs(len(a) - len(b)) > limit:
        return None
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
        if min(current) > limit:
            return None
        previous = current
    return previous[-1] if previous[-1] <= limit else None


@dataclass
class Normalised:
    text: str
    tokens: list[str]
    expansions: list[str] = field(default_factory=list)
    corrections: dict[str, str] = field(default_factory=dict)
    # Expansions of words the knowledge base does not know (for example Roman-Urdu
    # "tika"): these carry the meaning of the question and are weighted fully.
    strong: list[str] = field(default_factory=list)

    @property
    def terms(self) -> list[str]:
        """Stemmed content terms: original tokens first, then expansions."""
        return self.tokens + self.expansions


class Normaliser:
    """Normalise text against a vocabulary built from the knowledge corpus."""

    def __init__(self, vocabulary: Iterable[str] = ()):
        self.vocabulary: dict[str, int] = {}
        for word in vocabulary:
            self.vocabulary[word] = self.vocabulary.get(word, 0) + 1
        self._by_length: dict[int, list[str]] = {}
        for word in self.vocabulary:
            self._by_length.setdefault(len(word), []).append(word)

    def correct(self, word: str) -> str | None:
        if word in self.vocabulary or len(word) < 5 or word.isdigit():
            return None
        limit = 1 if len(word) <= 6 else 2
        best: tuple[int, int, str] | None = None
        for length in range(len(word) - limit, len(word) + limit + 1):
            for candidate in self._by_length.get(length, ()):
                if candidate[0] != word[0]:
                    continue
                distance = edit_distance_at_most(word, candidate, limit)
                if distance is None:
                    continue
                key = (distance, -self.vocabulary[candidate], candidate)
                if best is None or key < best:
                    best = key
        return best[2] if best else None

    def normalise(self, text: str, *, correct: bool = True) -> Normalised:
        folded = _fold(text)
        tokens: list[str] = []
        corrections: dict[str, str] = {}
        for token in raw_tokens(folded):
            token = WORDS.get(token, token)
            if token in STOPWORDS:
                continue
            stemmed = stem(token)
            if correct and self.vocabulary and stemmed not in self.vocabulary and token not in PHRASES:
                fixed = self.correct(stemmed)
                if fixed:
                    corrections[token] = fixed
                    stemmed = fixed
            tokens.append(stemmed)
        corrected_text = " ".join(corrections.get(t, t) for t in raw_tokens(folded))
        expansions = []
        strong: list[str] = []
        unknown = {t for t in raw_tokens(folded) if self.vocabulary and stem(WORDS.get(t, t)) not in self.vocabulary}
        for phrase, words in _phrase_expansions_with_keys(folded) + _phrase_expansions_with_keys(_fold(corrected_text)):
            is_strong = all(part in unknown for part in phrase.split())
            for word in words:
                word = WORDS.get(word, word)
                if word in STOPWORDS:
                    continue
                stemmed = stem(word)
                if stemmed not in tokens and stemmed not in expansions:
                    expansions.append(stemmed)
                if is_strong and stemmed not in strong:
                    strong.append(stemmed)
        return Normalised(text=text, tokens=tokens, expansions=expansions, corrections=corrections, strong=strong)


def index_terms(text: str) -> list[str]:
    """Terms for indexing corpus text: same pipeline, no spelling correction."""
    normalised = Normaliser().normalise(text, correct=False)
    return normalised.tokens + normalised.expansions
