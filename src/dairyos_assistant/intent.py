"""Intent and domain classification for operator questions.

This replaces the earlier keyword lists and single-purpose regexes with one
structured classifier. It scores a small set of feature families over the raw
text and the normalised terms, then decides an intent:

``DAIRYOS``          how DairyOS works: screens, workflows, calculations, data flow
``DAIRY``            general dairy husbandry and animal-health education
``HYBRID``           both, e.g. "what should I watch in a close-up cow and how does DairyOS track it"
``FARM_DATA``        a request for this farm's own records or figures
``CLINICAL``         a request for a medicine choice, dose or prescription
``INJECTION``        an attempt to change the Assistant's rules, identity or authority
``META``             greetings and "what can you do"
``OUT_OF_SCOPE``     unrelated general questions
``AMBIGUOUS``        too little to go on (a bare topic word)

The farm-data decision is deliberately narrow: it needs a *lookup form*
(how much / how many / which / list / show / status of a named animal) aimed at
the farm's own records, and it is suppressed by explanation forms ("how does
DairyOS calculate today's milk" is a product question). Personal framing alone
("my cow has a fever, what should I do") is not a data request; it is advice,
answered as education with the usual veterinary boundary.

Retrieval still runs for every intent, because even a refused request is
answered helpfully: where DairyOS shows the figure, or which knowledge applies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from dairyos_assistant.policy import REAL_IDENTIFIER
from dairyos_assistant.text import Normalised, stem

DAIRYOS_TERMS = frozenset(
    """dairyos software system app screen tab dashboard passport register ledger finance opex coml cop report reporting
    setting backup restore export import void amend correct edit entry enter record recorded save saved delete payroll
    analytic finding warning bell acknowledge reinstate tmr snapshot disposition reconciliation reconcile saleable
    wastage lot straw semen stock category categor lifecycle status frequency session sessions id prefix operator
    administrator password tab hide hidden email summary audit log calculate calculat formula attribution direct
    periodic allocat consumption official lock estimated schedule mark given occurrence yield watchlist
    non-opex expense revenue receivable payable sale purchase price manual storage override version stage module
    vwp eligibility pending due overdue count counted button tmr""".split()
)
DAIRY_TERMS = frozenset(
    """calf cow heifer bull buffalo colostrum navel wean starter scour diarrhea dehydrat pneumonia cough nasal fever
    temperature mastitis udder teat clot flake scc somatic milking routine dip strip cool chill fat snf ketosis
    milk-fever calcium hypocalcemia displaced abomasum metritis placenta afterbirth discharge dystocia calving
    birth labour labor close-up far-off dry-off transition fresh appetite rumen rumination manure dung bloat acidosis
    fibre fiber ration intake refusal sort bunk water drink heat estrus mount insemination conception gestation
    pregnancy abortion lame lameness hoof limp locomotion bcs condition thin fat comfort bedding lying ventilation
    shade fan panting stress vaccination vaccine booster biosecurity quarantine isolat parasite worm deworm tick
    fly fmd lsd hs brucell bvd ibr lepto disease sick ill dull weak down recumbent breathing welfare handling
    feed fodder silage hay grain concentrate nutrition mineral protein energy kam achanak""".split()
)
HEALTH_TERMS = frozenset(
    """sick ill fever temperature dull weak down recumbent cough nasal diarrhea scour bloat lame limp mastitis clot
    swollen swelling discharge not-eating appetite dehydrat pain bleeding abortion ketosis metritis placenta
    breathing panting disease infection lesion blister nodule died dead death""".split()
)

_DAIRYOS_EXPLICIT = re.compile(
    r"\b(?:dairy ?os|in the (?:app|software|system)|on (?:the )?(?:dashboard|screen)|which (?:tab|screen|report)|"
    r"where (?:do|can|should) i (?:record|enter|see|find|put|write)|how (?:do|can) i (?:record|enter|add|register|"
    r"correct|edit|void|delete|mark|change|close|find|see|export|print|pay|dry)|how to (?:record|enter|add|register|"
    r"correct|edit|void|delete|mark|change|set|close|find|see|export|print|pay|fill|clear)|record(?:ing)? (?:a|an|the|it|them)?|"
    r"entry|enter(?:ed)?)\b",
    re.I,
)
_DAIRYOS_DOMAIN_HINT = re.compile(
    r"\b(?:wrong|galat|mistake|incorrect|remove from (?:the )?sick list|recovered.*sick list|"
    r"vet(?:erinary)? bill|clinical treatment|health case|case id|withdrawal period start|"
    r"semen usage|expected dry.?off|delivery date|calf number|calf id|close\s+up|"
    r"close\s*-?\s*up.*categor|select close\s*-?\s*up.*ai|(?:where to|where do i) write litres?|"
    r"calved.*\bai\b|\bai\b.*calved|recovered.*sick list|remove.*sick list|"
    r"milk given to calves|milk used at home|milk thrown away|"
    r"doodh.*(?:kam|ghat)|galat litre|ghar ke liye doodh)\b",
    re.I,
)
_EXPLANATION = re.compile(
    r"\b(?:how (?:is|are|does|do|did)\b.{0,40}\b(?:calculat|work|determin|decide|count|handl|know|get|reach|go|flow|"
    r"affect|use|record|track)|what (?:does|is|are)\b.{0,30}\b(?:mean|meaning)|where does|why (?:is|are|does|isn|doesn|do|not)|"
    r"explain|how (?:do|can|should) i|where (?:do|can|should|is|are) i?|what happens)\b",
    re.I,
)
_LOOKUP = re.compile(
    r"\b(?:how (?:much|many)|which (?:\w+ ){0,3}?(?:cow|cows|animal|animals|heifer|heifers|calf|calves|bull|one|ones|"
    r"of (?:my|our|the) \w+)|list (?:all|my|our|the)|show (?:me )?(?:my|our|the|all|today|todays|today's)?|"
    r"give me (?:the|my|our|a) (?:list|figure|number|total)|(?:what is|what's|whats) (?:my|our|the farm's|today'?s)|"
    r"is \w+-\d+|(?:total|how much) .{0,20}(?:today|yesterday|this (?:week|month))|kitna|kitne|kaunsi|kon si|konsi)\b",
    re.I,
)
_FARM_POSSESSIVE = re.compile(
    r"\b(?:my|our|we|us|mine|ours|this farm|the farm'?s|on (?:the |my |our )?farm|in (?:the |my |our )?herd|hamari|hamara|mera|meri)\b",
    re.I,
)
_DEICTIC = re.compile(
    r"\b(?:today|todays|today's|yesterday|tonight|this (?:morning|week|month|year|season)|last (?:week|month|night)|"
    r"right now|currently|now|so far|aaj|abhi)\b",
    re.I,
)
_FARM_OBJECT = re.compile(
    r"\b(?:milk|litres?|liters?|production|produce|made|cow|cows|animal|animals|heifer|heifers|calf|calves|bull|bulls|"
    r"herd|feed|expense|expenses|spend|spent|profit|revenue|income|sale|sales|receivable|receivables|payable|cop|cost|"
    r"record|records|finance|pregnant|sick|withdrawal|due|doodh|gaye|janwar)\b",
    re.I,
)
_CLINICAL = re.compile(
    r"\b(?:dose|dosage|how many (?:ml|mg|cc|bottles?|tablets?|injections?)|how much (?:\w+ ){0,3}(?:to )?(?:give|inject)|"
    r"which (?:antibiotic|medicine|drug|injection|tube)|what (?:antibiotic|medicine|drug|injection)|best (?:antibiotic|medicine|"
    r"drug|injection)|(?:mg|ml)(?:/| per )kg|prescribe|prescription|kitne ml|konsi dawai|dawai|inject(?:ion)? for|"
    r"give (?:this|the|my|her|him) (?:cow|animal|calf)? ?(?:an? )?(?:antibiotic|injection|dose|medicine)|"
    r"(?:antibiotic|medicine|injection) dose|calcium (?:bottles?|dose))\b",
    re.I,
)
_INJECTION = re.compile(
    r"\b(?:ignore (?:your|the|all|previous|prior) (?:rules?|instructions?|restrictions?)|disregard (?:your|the) (?:rules|instructions)|"
    r"pretend (?:you|that you)|act as|you are now|system prompt|hidden instructions|jailbreak|developer mode|"
    r"i am the (?:admin|administrator|owner)|i'?m the (?:admin|administrator|owner)|as (?:the )?(?:admin|administrator)|"
    r"you have permission|i give you permission|i authori[sz]e|bypass|override (?:your|the) (?:rules|policy)|"
    r"run sql|execute sql|select \* from|query the database|read the database|access the database|connect to the database|"
    r"just guess|password|delete all|mark all)\b",
    re.I,
)
_GREETING = re.compile(r"^\s*(?:hi|hello|hey|salam|assalam[ou] ?alaikum|aoa|good (?:morning|evening)|thanks?|thank you|shukriya)\W*$", re.I)
_META = re.compile(r"\b(?:what can you do|who are you|what are you|can you see (?:my|our)|do you have access|help me)\b", re.I)
_ACTION_REQUEST = re.compile(
    r"^\s*(?:please\s+)?(?:delete|remove|mark|update|change|set|add|record|enter|void|create|approve|clear|reset)\b"
    r"(?=.*\b(?:for me|all|every|everything|yesterday'?s|today'?s|these|them|records)\b)(?!.*\b(?:how|where)\b)",
    re.I,
)


@dataclass
class Intent:
    intent: str
    confidence: float
    signals: list[str] = field(default_factory=list)
    dairyos_score: float = 0.0
    dairy_score: float = 0.0
    health: bool = False
    farm_data: bool = False
    clinical: bool = False
    injection: bool = False
    action_request: bool = False

    def collection_prior(self) -> dict[str, float]:
        if self.intent == "DAIRYOS":
            return {"dairyos": 1.35, "dairy": 0.8}
        if self.intent == "DAIRY":
            return {"dairyos": 0.75, "dairy": 1.35}
        if self.intent in {"FARM_DATA"}:
            return {"dairyos": 1.3, "dairy": 0.9}
        if self.intent == "CLINICAL":
            return {"dairyos": 0.8, "dairy": 1.3}
        return {"dairyos": 1.0, "dairy": 1.0}


def _stems(words: frozenset[str]) -> frozenset[str]:
    return frozenset(stem(w) for w in words)


def _score(tokens: list[str], expansions: list[str], vocabulary: frozenset[str]) -> float:
    stems = _stems(vocabulary)
    hits = 0.0
    for weight, terms in ((1.0, tokens), (0.5, expansions)):
        for term in set(terms):
            if term in vocabulary or term in stems:
                hits += weight
            elif len(term) >= 4 and any(term.startswith(v) or v.startswith(term) for v in stems if len(v) >= 4):
                hits += 0.6 * weight
    return hits


def classify(question: str, normalised: Normalised) -> Intent:
    text = question or ""
    terms = set(normalised.tokens) | set(normalised.expansions)
    signals: list[str] = []

    dairyos = _score(normalised.tokens, normalised.expansions, DAIRYOS_TERMS)
    dairy = _score(normalised.tokens, normalised.expansions, DAIRY_TERMS)
    if _DAIRYOS_EXPLICIT.search(text):
        dairyos += 2.0
        signals.append("dairyos-workflow-form")
    if _DAIRYOS_DOMAIN_HINT.search(text):
        dairyos += 3.0
        signals.append("dairyos-domain-hint")
    if re.search(r"\bdairy ?os\b", text, re.I):
        dairyos += 3.0
        signals.append("names-dairyos")
    health = bool(terms & HEALTH_TERMS) or any(t.startswith(("dehydrat", "swell", "diarrh", "fever", "sick")) for t in terms)

    injection = bool(_INJECTION.search(text))
    clinical = bool(_CLINICAL.search(text))
    dairyos_domain_hint = bool(_DAIRYOS_DOMAIN_HINT.search(text))
    explanation = bool(_EXPLANATION.search(text))
    lookup = bool(_LOOKUP.search(text))
    possessive = bool(_FARM_POSSESSIVE.search(text))
    deictic = bool(_DEICTIC.search(text))
    farm_object = bool(_FARM_OBJECT.search(text))
    identifier = bool(REAL_IDENTIFIER.search(text) or re.search(r"\b(?:cow|animal|tag) ?#?\d{2,}\b", text, re.I))
    action_request = bool(_ACTION_REQUEST.search(text)) and not explanation and not re.search(r"\?\s*$", text)

    farm_data = False
    if lookup and farm_object and (possessive or deictic or identifier or re.search(r"\b(?:we|us)\b", text, re.I)):
        farm_data = True
    if lookup and re.search(r"\b(?:which|list|show|kaunsi|konsi|kon si)\b", text, re.I) and farm_object and not explanation:
        farm_data = True
    if identifier and farm_object and not explanation:
        farm_data = True
    if deictic and farm_object and re.search(r"\b(?:how much|how many|total|what(?:'s| is)|kitna)\b", text, re.I):
        farm_data = True
    if explanation and not re.search(r"\b(?:how (?:much|many)|which of)\b", text, re.I):
        farm_data = False
    if re.search(r"\b(?:which|what) report\b|\breport shows\b|\bwhere is the report\b", text, re.I):
        farm_data = False
    if farm_data:
        signals.append("farm-data-lookup")

    if injection:
        signals.append("injection-or-authority-claim")
    if clinical:
        signals.append("clinical-prescription")
    if health:
        signals.append("animal-health")

    content_terms = [t for t in normalised.tokens if not t.isdigit()]
    if _GREETING.match(text) or (_META.search(text) and not farm_data):
        intent, confidence = "META", 0.9
    elif injection and (farm_data or "password" in text.lower() or "prompt" in text.lower() or action_request
                        or re.search(r"database|sql|delete|mark all|guess", text, re.I)):
        intent, confidence = "INJECTION", 0.95
    elif farm_data:
        intent, confidence = "FARM_DATA", 0.85
    elif action_request and dairyos >= 1:
        intent, confidence = "INJECTION", 0.7  # asked to act on records; the Assistant cannot
        signals.append("action-request")
    elif clinical:
        intent, confidence = "CLINICAL", 0.9
    elif dairyos_domain_hint:
        intent, confidence = "DAIRYOS", 0.9
    elif injection:
        intent, confidence = "INJECTION", 0.8
    elif dairyos == 0 and dairy == 0:
        intent, confidence = ("AMBIGUOUS", 0.4) if len(content_terms) <= 1 else ("OUT_OF_SCOPE", 0.6)
    elif len(content_terms) <= 1 and not health:
        intent, confidence = "AMBIGUOUS", 0.5
    elif dairyos >= 2 and dairy >= 2 and (re.search(r"\bdairy ?os\b", text, re.I) or health):
        intent, confidence = "HYBRID", 0.7
    elif health and dairyos < 2.5:
        intent, confidence = "DAIRY", 0.75
    elif dairyos > dairy:
        intent, confidence = "DAIRYOS", min(0.95, 0.5 + 0.1 * (dairyos - dairy))
    elif dairy > dairyos:
        intent, confidence = "DAIRY", min(0.95, 0.5 + 0.1 * (dairy - dairyos))
    else:
        intent, confidence = "HYBRID", 0.5

    return Intent(
        intent=intent, confidence=round(confidence, 2), signals=signals, dairyos_score=round(dairyos, 2),
        dairy_score=round(dairy, 2), health=health, farm_data=farm_data, clinical=clinical,
        injection=injection, action_request=action_request,
    )
