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
        dct.pop('__annotations__', None)
        return super().__new__(cls, name, bases, dct)


class C(BaseConstants):
    NAME_IN_URL = 'pictionary'
    PLAYERS_PER_GROUP = 2
    NUM_PRACTICE_ROUNDS = 0
    # how many stimuli in each phase
    NUM_PHASE_STIMS = [
        len(PHASES[0]),
        len(PHASES[1]),
        len(PHASES[2]),
    ]

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

def creating_session(subsession: Subsession):
    # not yet implemented
    subsession.is_practice_round = (
        subsession.round_number <= C.NUM_PRACTICE_ROUNDS
    )
    # get the real round number
    if not subsession.is_practice_round:
        subsession.real_round_number = (
            subsession.round_number - C.NUM_PRACTICE_ROUNDS
        )
    # set the current round
    if 'current_phase' not in subsession.session.vars or subsession.session.vars['current_phase'] is None:
        subsession.session.vars['current_phase'] = 0
    
    # if we're in a practice round, we don't need to do anything else
    if subsession.is_practice_round:
        return
    
    # if the stim list is empty, we need to load the stims
    if 'stim_order' not in subsession.session.vars or subsession.session.vars['stim_order'] is None:
        # load the stims and randomize for all phases
        stims = []
        for i, phase in enumerate(PHASES):
            phase_stims = phase * C.PHASE_STIM_REPEATS[i]
            shuffle(phase_stims)
            stims.extend(phase_stims)

        subsession.session.vars['stim_order'] = stims
    
    # pick a starting player
    subsession.starting_player = randint(0, C.PLAYERS_PER_GROUP - 1)

class Player(BasePlayer, metaclass=AnnotationFreeMeta):
    choice: int = models.IntegerField()
    is_drawer: bool = models.BooleanField()


class Group(BaseGroup):
    wait_for_ids: str = models.LongStringField(initial='[]')
    arrived_ids: str = models.LongStringField(initial='[]')


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
        return player.round_number == 1 and player.session.vars['current_phase'] == 0

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
        if data.get('type') == 'wait_page':
            return wait_page_live_method(player, data)

    @staticmethod
    def error_message(player: Player, values):
        group = player.group
        if unarrived_players(group):
            return "Wait page not finished"


class ThankYou(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.session.vars['current_phase'] == 2

class Selecting(Page):
    pass

class RoundComplete(Page):
    pass

# PAGES
class Drawing(Page):
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
            current_phase=player.session.vars['current_phase'],
        )


page_sequence = [Welcome, Instructions, Waiting, Drawing, Selecting, RoundComplete, ThankYou]