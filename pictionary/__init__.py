from sqlalchemy.ext.declarative import DeclarativeMeta  # type: ignore
from otree.api import BaseConstants, BaseSubsession, BaseGroup, BasePlayer, models, Page, ExtraModel, WaitPage  # type: ignore
from .stims import PHASES
from json import dumps as json_dumps, loads as json_loads
from random import shuffle, randint
import base64


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
    NUM_PHASE_TRIALS = [x * y for x, y in zip(NUM_PHASE_STIMS, PHASE_STIM_REPEATS)]
    # We can't repeat the app so we need to use the rounds as phases
    NUM_ROUNDS = 3


class Subsession(BaseSubsession, metaclass=AnnotationFreeMeta):
    phase: int = models.IntegerField()
    stim_order: str = models.LongStringField(initial="[]")
    current_trial: int = models.IntegerField(initial=1)


class Player(BasePlayer, metaclass=AnnotationFreeMeta):
    pass


class Group(BaseGroup, metaclass=AnnotationFreeMeta):
    pass


class PictionaryDrawing(ExtraModel):
    svg = models.LongStringField(initial="")
    completed = models.BooleanField(initial=False)


class PictionaryResponse(ExtraModel):
    response = models.StringField(initial="")
    correct = models.BooleanField(initial=False)
    completed = models.BooleanField(initial=False)


class PictionaryTrial(ExtraModel):
    subsess = models.Link(Subsession)
    drawing = models.Link(PictionaryDrawing)
    response = models.Link(PictionaryResponse)
    drawer = models.Link(Player)
    responder = models.Link(Player)
    stim = models.StringField()
    concepts = models.LongStringField()
    trial = models.IntegerField()
    phase = models.IntegerField()





# runs on each round
def creating_session(subsession: Subsession):
    players: list[Player] = subsession.get_players()
    print(f"Loading stimuli and randomizing order for round {subsession.round_number}")
    # load the stims and randomize for all phases
    phase_stims = PHASES[subsession.round_number - 1] * C.PHASE_STIM_REPEATS[subsession.round_number - 1]
    shuffle(phase_stims)
    subsession.stim_order = json_dumps(phase_stims)
    # Prepare all the rounds
    drawing_player = randint(0, 1)
    print(f"Creating trials for phase {subsession.round_number}")
    for trial, stim in enumerate(phase_stims):
        print(f"{trial + 1}...", end="")
        # create the round
        PictionaryTrial().create(
            subsess = subsession,
            drawing = PictionaryDrawing().create(),
            response = PictionaryResponse().create(),
            stim = stim[0],
            concepts = json_dumps(stim[1]),
            phase = subsession.round_number,
            drawer = players[drawing_player],
            responder = players[1 - drawing_player],
            trial = trial + 1,
        )
        # flip the drawing player
        drawing_player = 1 - drawing_player
    print("done")


# returns the partner of the player
def get_partner(player: Player):
    return player.get_others_in_group()[0]


# PAGES
class ExperimentWelcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        # only show the welcome page on the first round of the FIRST phase
        return player.round_number == 1 and player.subsession.round_number == 1

class PhaseInstructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        # show the instrunctions on the first round of EACH phase
        return player.round_number == 1


class Waiting(WaitPage):
    pass


class ExperimentThankYou(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.subsession.round_number == C.NUM_ROUNDS

# determine if the current player is the drawer without messing up the data
def is_drawer(player: Player, trial: PictionaryTrial):
    return player.id_in_group == trial.drawer.id_in_group


def is_last_round(player: Player):
    return player.subsession.round_number == C.NUM_ROUNDS

def get_current_trial(player: Player) -> PictionaryTrial:
    print(player.subsession, player.subsession.current_trial, player.subsession.round_number)
    return PictionaryTrial.filter(subsess=player.subsession, trial=player.subsession.current_trial)[0]


def get_stim_list(player: Player):
    stims = PHASES[player.subsession.round_number - 1]
    # we only need the first element of each stim
    return [stim[0] for stim in stims]

class PhaseComplete(Page):
    pass

class Drawing(Page):
    # @staticmethod
    # def is_displayed(player: Player):
    #     return is_drawer(player)

    @staticmethod
    def before_next_page(player, timeout_happened):
        pass

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            current_phase=player.subsession.round_number,
            stims=PHASES[player.subsession.round_number - 1],
            blur=player.session.config.get("blur", True),
            live_draw=player.session.config.get("live_draw", True),
        )

    @staticmethod
    def live_method(player, data):
        trial = get_current_trial(player)
        drawing_player = is_drawer(player, trial)
        selected_stim = ""
        stim_list = get_stim_list(player)
        if drawing_player:
            selected_stim = trial.stim
            
        if "event" in data:
            if data["event"] == "init":
                print("received init from ", player.id_in_group)
                return {
                    player.id_in_group: dict(
                        event='init',
                        drawer=drawing_player,
                        # this allows recovery / in case of browser reload
                        drawing=base64.b64encode(trial.drawing.svg.encode('utf-8')).decode('utf-8'),
                        completed=trial.drawing.completed,
                        stims=stim_list,
                        selected_stim=selected_stim,
                    )
                }
            elif data["event"] == "update":
                if drawing_player:
                    print("updating drawing for ", player.id_in_group)
                    trial.drawing.svg = base64.b64decode(data["drawing"]).decode('utf-8')
            elif data["event"] == "drawing_complete":
                if drawing_player:
                    partner = get_partner(player)
                    print("received drawing from ", player.id_in_group)
                    trial.drawing.svg = base64.b64decode(data["drawing"]).decode('utf-8')
                    trial.drawing.completed = True
                    return {
                        partner.id_in_group: dict(
                            event='drawing_complete',
                            drawer=False,
                            drawing=data["drawing"],
                            completed = True,
                            stims=get_stim_list(player),
                        )}
            elif data["event"] == "stimulus_selected": # just a click, not the "completed" event
                if not drawing_player:
                    print(f"received stimulus selection ({data['stim']}) from {player.id_in_group}")
                    trial.stim = data["stim"]
                    
            elif data["event"] == "response_complete":
                if not drawing_player:
                    print(f"received response from {player.id_in_group}")
                    trial.response.response = data["stim"]
                    trial.response.correct = data["stim"] == trial.stim
                    trial.response.completed = True
                    return {
                        0: dict(
                            event='show_response',
                            response=data["response"],
                            correct=data["correct"],
                            stims=get_stim_list(player),
                            completed=True,
                        )
                    }
                    
                # print('received drawing from ', player.id_in_group, ':', data)
                # if player.session.config.get("live_draw", True):
                #     # send the drawing to the partner
                #     partner = get_partner(player)
                #     return {partner.id_in_group: dict(drawing=data)}

            


page_sequence = [
    ExperimentWelcome,
    PhaseInstructions,
    Waiting,
    # this page will repeat for the number of rounds in each phase
    Drawing,
    PhaseComplete,
    ExperimentThankYou,
]
