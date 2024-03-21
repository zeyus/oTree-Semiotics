"""This could be JSON or in the database, for now, let's just define it here"""

PRONOUN: list[str] = [
    "1st person",
    "2nd person",
]

TENSE: list[str] = [
    "present",
    "past",
]

MODALITY: list[str] = [
    "obligation",
    "possibility",
]

ASPECT: list[str] = [
    "simple",
    "perfect"
]

PHASE_1: list[tuple[str, list[str]]] = [
    # first person
    ("I eat the ice cream", [PRONOUN[0]]),
    ("I kick the ball", [PRONOUN[0]]),
    ("I see the bird", [PRONOUN[0]]),

    # second person
    ("You eat the ice cream", [PRONOUN[1]]),
    ("You kick the ball", [PRONOUN[1]]),
    ("You see the bird", [PRONOUN[1]]),
]

PHASE_2: list[tuple[str, list[str]]] = [
    # first person present
    ("I eat the ice cream", [PRONOUN[0], TENSE[0]]),
    ("I kick the ball", [PRONOUN[0], TENSE[0]]),
    ("I see the bird", [PRONOUN[0], TENSE[0]]),
    
    # first person past
    ("I ate the ice cream", [PRONOUN[0], TENSE[1]]),
    ("I kicked the ball", [PRONOUN[0], TENSE[1]]),
    ("I saw the bird", [PRONOUN[0], TENSE[1]]),

    # second person present
    ("You eat the ice cream", [PRONOUN[1], TENSE[0]]),
    ("You kick the ball", [PRONOUN[1], TENSE[0]]),
    ("You see the bird", [PRONOUN[1], TENSE[0]]),

    # second person past
    ("You ate the ice cream", [PRONOUN[1], TENSE[1]]),
    ("You kicked the ball", [PRONOUN[1], TENSE[1]]),
    ("You saw the bird", [PRONOUN[1], TENSE[1]]),
]

PHASE_3: list[tuple[str, list[str]]] = [
    # first person present obligation simple
    ("I should eat the ice cream", [PRONOUN[0], TENSE[0], MODALITY[0], ASPECT[0]]),
    ("I should kick the ball", [PRONOUN[0], TENSE[0], MODALITY[0], ASPECT[0]]),
    ("I should see the bird", [PRONOUN[0], TENSE[0], MODALITY[0], ASPECT[0]]),

    # second person present obligation simple
    ("You should eat the ice cream", [PRONOUN[1], TENSE[0], MODALITY[0], ASPECT[0]]),
    ("You should kick the ball", [PRONOUN[1], TENSE[0], MODALITY[0], ASPECT[0]]),
    ("You should see the bird", [PRONOUN[1], TENSE[0], MODALITY[0], ASPECT[0]]),

    # first person past obligation perfect
    ("I should have eaten the ice cream", [PRONOUN[0], TENSE[1], MODALITY[0], ASPECT[1]]),
    ("I should have kicked the ball", [PRONOUN[0], TENSE[1], MODALITY[0], ASPECT[1]]),
    ("I should have seen the bird", [PRONOUN[0], TENSE[1], MODALITY[0], ASPECT[1]]),

    # second person past obligation perfect
    ("You should have eaten the ice cream", [PRONOUN[1], TENSE[1], MODALITY[0], ASPECT[1]]),
    ("You should have kicked the ball", [PRONOUN[1], TENSE[1], MODALITY[0], ASPECT[1]]),
    ("You should have seen the bird", [PRONOUN[1], TENSE[1], MODALITY[0], ASPECT[1]]),

    # first person present possibility simple
    ("I could eat the ice cream", [PRONOUN[0], TENSE[0], MODALITY[1], ASPECT[0]]),
    ("I could kick the ball", [PRONOUN[0], TENSE[0], MODALITY[1], ASPECT[0]]),
    ("I could see the bird", [PRONOUN[0], TENSE[0], MODALITY[1], ASPECT[0]]),

    # second person present possibility simple
    ("You could eat the ice cream", [PRONOUN[1], TENSE[0], MODALITY[1], ASPECT[0]]),
    ("You could kick the ball", [PRONOUN[1], TENSE[0], MODALITY[1], ASPECT[0]]),
    ("You could see the bird", [PRONOUN[1], TENSE[0], MODALITY[1], ASPECT[0]]),

    # first person past possibility perfect
    ("I could have eaten the ice cream", [PRONOUN[0], TENSE[1], MODALITY[1], ASPECT[1]]),
    ("I could have kicked the ball", [PRONOUN[0], TENSE[1], MODALITY[1], ASPECT[1]]),
    ("I could have seen the bird", [PRONOUN[0], TENSE[1], MODALITY[1], ASPECT[1]]),

    # second person past possibility perfect
    ("You could have eaten the ice cream", [PRONOUN[1], TENSE[1], MODALITY[1], ASPECT[1]]),
    ("You could have kicked the ball", [PRONOUN[1], TENSE[1], MODALITY[1], ASPECT[1]]),
    ("You could have seen the bird", [PRONOUN[1], TENSE[1], MODALITY[1], ASPECT[1]]),
]


PHASES: list[list[tuple[str, list[str]]]] = [PHASE_1, PHASE_2, PHASE_3]
