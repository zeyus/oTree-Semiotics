from sqlalchemy.ext.declarative import DeclarativeMeta  # type: ignore
from otree.api import BaseConstants, BaseSubsession, BaseGroup, BasePlayer, models, Page  # type: ignore
from .stims import PHASES
from json import dumps as json_dumps, loads as json_loads
from random import shuffle, randint


doc = """
... Description of the game
"""


class AnnotationFreeMeta(DeclarativeMeta):
    """Metaclass to remove the __annotations__ attribute from the class
    this fixes an error where oTree tries to use __annotations__ and thinks it's a dict
    that needs saving.
    """

    def __new__(cls, name, bases, dct):
        dct.pop("__annotations__", None)
        return super().__new__(cls, name, bases, dct)


class C(BaseConstants):
    NAME_IN_URL = "pictionary"
    PLAYERS_PER_GROUP = 2
    NUM_PRACTICE_ROUNDS = 0
    # how many stimuli in each phase
    NUM_PHASE_STIMS = [len(phase) for phase in PHASES]

    # how many times to repeat each item in each phase
    PHASE_STIM_REPEATS = [
        3,
        1,
        1,
    ]
    # technichally not constants, but still deterministic
    NUM_PHASE_ROUNDS = [x * y for x, y in zip(NUM_PHASE_STIMS, PHASE_STIM_REPEATS)]
    # set this to the max, we stop early if we run out of rounds
    NUM_ROUNDS = max(NUM_PHASE_ROUNDS) + NUM_PRACTICE_ROUNDS


class Subsession(BaseSubsession, metaclass=AnnotationFreeMeta):
    is_practice_round: bool = models.BooleanField()
    real_round_number: int = models.IntegerField()
    stim: str = models.StringField(initial="")
    concepts: str = models.LongStringField(initial="")


class Player(BasePlayer, metaclass=AnnotationFreeMeta):
    choice: int = models.IntegerField()


class Group(BaseGroup, metaclass=AnnotationFreeMeta):
    wait_for_ids: str = models.LongStringField(initial="[]")
    arrived_ids: str = models.LongStringField(initial="[]")


# runs on each round
def creating_session(subsession: Subsession):
    # not yet implemented
    subsession.is_practice_round = subsession.round_number <= C.NUM_PRACTICE_ROUNDS
    # get the real round number
    if not subsession.is_practice_round:
        subsession.real_round_number = subsession.round_number - C.NUM_PRACTICE_ROUNDS

    players: list[Player] = subsession.get_players()
    # set the starting phase and player, this will only happen once
    if (
        "current_phase" not in subsession.session.vars
        or subsession.session.vars["current_phase"] is None
    ):
        print("Initialising phase 0")
        subsession.session.vars["current_phase"] = 0
        # pick a starting player
        shuffle(players)
        for i, player in enumerate(players):
            player.participant.vars["starting_player"] = i == 0
            print(f"Player {i} is starting player: {player.participant.vars['starting_player']}")
            # initialize the drawings_completed field
            player.participant.vars["drawings_completed"] = 0

    # if the stim list is empty, we need to load the stims, this also will only happen once
    if (
        "stim_order" not in subsession.session.vars
        or subsession.session.vars["stim_order"] is None
    ):
        print("Loading stimuli and randomizing order")
        # load the stims and randomize for all phases
        stims = []
        for i, phase in enumerate(PHASES):
            phase_stims = phase * C.PHASE_STIM_REPEATS[i]
            shuffle(phase_stims)
            stims.append(phase_stims)

        subsession.session.vars["stim_order"] = stims
    
    # get the current stim
    current_stim = None
    try:
        current_stim = subsession.session.vars["stim_order"][subsession.session.vars["current_phase"]].pop()
        subsession.stim = current_stim[0]
        subsession.concepts = ", ".join(current_stim[1])
        print (f"Phase {subsession.session.vars['current_phase']+1} Stim added: {subsession.stim}, Concepts: {subsession.concepts}")
    except IndexError:
        subsession.stim = ""
        subsession.concepts = ""
        print("No more stimuli for this phase")




def unarrived_players(group: Group):
    return set(json_loads(group.wait_for_ids)) - set(json_loads(group.arrived_ids))


def wait_page_live_method(player: Player, data):
    group = player.group

    arrived_ids_set = set(json_loads(group.arrived_ids))
    arrived_ids_set.add(player.id_in_subsession)
    group.arrived_ids = json_dumps(list(arrived_ids_set))

    if not unarrived_players(group):
        return {0: dict(finished=True)}


def get_partner(player: Player):
    return player.get_others_in_group()[0]


class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        # only show the welcome page on the first round of the first phase
        return player.round_number == 1 and player.session.vars["current_phase"] == 0


class Instructions(Page):
    pass


class Waiting(Page):
    @staticmethod
    def is_displayed(player: Player):
        group = player.group
        # first time
        if not json_loads(group.wait_for_ids):
            wait_for_ids = [p.id_in_subsession for p in group.get_players()]
            group.wait_for_ids = json_dumps(wait_for_ids)
        return unarrived_players(group)

    @staticmethod
    def live_method(player: Player, data):
        if data.get("type") == "wait_page":
            return wait_page_live_method(player, data)

    @staticmethod
    def error_message(player: Player, values):
        group = player.group
        if unarrived_players(group):
            return "Wait page not finished"


class ThankYou(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.session.vars["current_phase"] == 2

# determine if the current player is the drawer without messing up the data
def is_drawer(player: Player):
    return (
            player.participant.vars["starting_player"] and player.subsession.round_number % 2 == 1
        ) or (
            not player.participant.vars["starting_player"] and player.subsession.round_number % 2 == 0
        )

class Selecting(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not is_drawer(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            stim=player.subsession.stim,
        )
class RoundComplete(Page):
    pass


# PAGES
class Drawing(Page):
    @staticmethod
    # def is_displayed(player: Player):
    #     return is_drawer(player)

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.vars["drawings_completed"] += 1

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        my_partner_previous = partner.in_all_rounds()
        my_previous_partners = [
            get_partner(me_prev) for me_prev in player.in_all_rounds()
        ]

        return dict(
            partner=partner,
            my_partner_previous=my_partner_previous,
            my_previous_partners=my_previous_partners,
            current_phase=player.session.vars["current_phase"] + 1,
            stim=player.subsession.stim,
            is_drawer=is_drawer(player),
            blur=player.session.config.get("blur", True),
            live_draw=player.session.config.get("live_draw", True),
        )

    @staticmethod
    def live_method(player, data):
        if is_drawer(player):
            print('received drawing from ', player.id_in_group, ':', data)
            if player.session.config.get("live_draw", True):
                # send the drawing to the partner
                partner = get_partner(player)
                return {partner.id_in_group: dict(drawing=data)}
        else:
            print('received answer from ', player.id_in_group, ':', data)
            


page_sequence = [
    Welcome,
    Instructions,
    Waiting,
    Drawing,
    # let's have both on the drawing page just use "is_drawer" to determine which to show
    # Selecting,
    RoundComplete,
    ThankYou,
]
