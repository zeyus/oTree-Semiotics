from sqlalchemy.ext.declarative import DeclarativeMeta  # type: ignore
from otree.api import BaseConstants, BaseSubsession, BaseGroup, BasePlayer, models, Page, ExtraModel, WaitPage  # type: ignore
from otree.models import Participant  # type: ignore
from otree.common import expand_choice_tuples  # type: ignore
from .stims import PHASES
from json import dumps as json_dumps, loads as json_loads
from random import shuffle, randint
import base64
import datetime


doc = """
Paired drawing task where one player draws a concept and the other player guesses the concept.
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
    # Time limit for drawing
    DRAWING_TIME = 120


class Subsession(BaseSubsession, metaclass=AnnotationFreeMeta):
    pass


class Player(BasePlayer, metaclass=AnnotationFreeMeta):
    ready: bool = models.BooleanField(initial=False)  # type: ignore
    age = models.IntegerField(
        label='Your age',
        min=18, max=99)
    gender = models.IntegerField(
        label='Your gender',
        choices=[
            [0, 'Prefer not to say'],
            [1, 'Female'],
            [2, 'Male'],
            [3, 'Non-binary'],
            [4, 'Other']
        ]
    )
    native_language = models.StringField(
        label='What is your native language?',
        choices=[
            'Danish',
            'English',
            'French',
            'German',
            'Spanish',
            'Swedish',
            'Other'
        ]
    )
    language_other = models.StringField(
        label='If you selected "Other", please specify:',
        blank=True
    )

    # post experiment survey
    # in your drawings, how did you represent/distinguish between:
    # - I/you?
    # - Present tense/past tense?
    # - Could/should?

    i_you = models.LongStringField(
        label='In your drawings, how did you represent/distinguish between "I" and "you"?'
    )
    present_past = models.LongStringField(
        label='In your drawings, how did you represent/distinguish between present and past tense?'
    )
    could_should = models.LongStringField(
        label='In your drawings, how did you represent/distinguish between "could" and "should"?'
    )

    # workaround / hack for previous values that don't exist
    def field_display(self, name):
        value = getattr(self, name)
        target = self.get_user_defined_target()
        choices_func = getattr(target, name + '_choices', None)
        if choices_func:
            choices = choices_func(self)
        else:
            choices = getattr(type(self), name).form_props['choices']
        choice_dict = dict(expand_choice_tuples(choices))
        try:
            return choice_dict[value]
        except KeyError:
            return "N/A"

class Group(BaseGroup, metaclass=AnnotationFreeMeta):
    phase: int = models.IntegerField()
    stim_order: str = models.LongStringField(initial="[]")  # type: ignore
    current_trial: int = models.IntegerField(initial=1)  # type: ignore


class PictionaryDrawing(ExtraModel):
    svg = models.LongStringField(initial="")  # type: ignore
    completed = models.BooleanField(initial=False)  # type: ignore
    drawing_time = models.FloatField(initial=0.0)  # type: ignore
    start_timestamp = models.FloatField(initial=0.0)  # type: ignore


class PictionaryResponse(ExtraModel):
    response = models.StringField(initial="")  # type: ignore
    correct = models.BooleanField(initial=False)  # type: ignore
    completed = models.BooleanField(initial=False)  # type: ignore


class PictionaryTrial(ExtraModel, metaclass=AnnotationFreeMeta):
    subsess: Subsession = models.Link(Subsession)
    group: Group = models.Link(Group)
    drawing: PictionaryDrawing = models.Link(PictionaryDrawing)
    response: PictionaryResponse = models.Link(PictionaryResponse)
    drawer: Player = models.Link(Player)
    responder: Player = models.Link(Player)
    stim: str = models.StringField()
    concepts: str = models.LongStringField()
    trial: int = models.IntegerField()
    phase: int = models.IntegerField()
    completed: bool = models.BooleanField(initial=False)  # type: ignore


# runs on each round
def creating_session(subsession: Subsession):
    players: list[Player] = subsession.get_players()
    print(f"Loading stimuli and randomizing order for round {subsession.round_number}")

    # load the stims and randomize for all phases
    phase_stims = PHASES[subsession.round_number - 1] * C.PHASE_STIM_REPEATS[subsession.round_number - 1]

    groups = subsession.get_groups()
    for group in groups:
        shuffle(phase_stims)
        group.stim_order = ", ".join([stim[0] for stim in phase_stims])
        # Prepare all the rounds
        drawing_player = randint(0, 1)
        print(f"Creating trials for phase {subsession.round_number}")
        for trial, stim in enumerate(phase_stims):
            print(f"{trial + 1}...", end="")
            # create the round
            PictionaryTrial().create(
                subsess = subsession,
                group = group,
                drawing = PictionaryDrawing().create(),
                response = PictionaryResponse().create(),
                stim = stim[0],
                concepts = ", ".join(stim[1]),
                phase = subsession.round_number,
                drawer = players[drawing_player],
                responder = players[1 - drawing_player],
                trial = trial + 1,
                completed = False,
            )
            # flip the drawing player
            drawing_player = 1 - drawing_player
    print("done")


# returns the partner of the player
def get_partner(player: Player):
    return player.get_others_in_group()[0]


# PAGES
class ExperimentWelcome(Page):
    form_model = 'player'
    form_fields = ['age', 'gender', 'native_language', 'language_other']
    @staticmethod
    def is_displayed(player: Player):
        # only show the welcome page on the first round of the FIRST phase
        return player.subsession.round_number == 1


class PostExperimentSurvey(Page):
    form_model = 'player'
    form_fields = ['i_you', 'present_past', 'could_should']
    @staticmethod
    def is_displayed(player: Player):
        # only show the survey at the end of the last last phase
        return player.subsession.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # add the post experiment survey data to all all arounds
        # hacky but it works
        
        # round one has demographic data, but post experiment survey
        r1p = player.in_round(1)

        # round 2 player has neither
        r2p = player.in_round(2)

        r1p.i_you = player.i_you
        r1p.present_past = player.present_past
        r1p.could_should = player.could_should
        
        r2p.age = r1p.age
        r2p.gender = r1p.gender
        r2p.native_language = r1p.native_language
        r2p.language_other = r1p.language_other
        r2p.i_you = player.i_you
        r2p.present_past = player.present_past
        r2p.could_should = player.could_should

        # round 3 player has no demographic data, but post experiment survey
        player.age = r1p.age
        player.gender = r1p.gender
        player.native_language = r1p.native_language
        player.language_other = r1p.language_other
        

class PhaseInstructions(Page):
    pass

class Waiting(WaitPage):
    pass

class ExperimentThankYou(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.subsession.round_number == C.NUM_ROUNDS

# determine if the current player is the drawer without messing up the data
def is_drawer(player: Player, trial: PictionaryTrial):
    return player.id_in_group == trial.drawer.id_in_group


def is_phase_complete(player: Player):
    complete = player.group.current_trial > C.NUM_PHASE_TRIALS[player.subsession.round_number - 1]
    print("is phase complete", complete)
    return complete

def get_current_trial(player: Player) -> PictionaryTrial:
    print("getting current trial", player.group.current_trial)
    return PictionaryTrial.filter(group=player.group, subsess=player.subsession, trial=player.group.current_trial)[0]


def get_stim_list(player: Player, randomize=False):
    stims = PHASES[player.subsession.round_number - 1]
    # we only need the first element of each stim
    stims = [stim[0] for stim in stims]
    if randomize:
        shuffle(stims)
    return stims

class PhaseComplete(Page):
    pass

class Drawing(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not is_phase_complete(player)

    @staticmethod
    def before_next_page(player, timeout_happened = False):
        player.ready = False

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            current_phase=player.subsession.round_number,
            stims=PHASES[player.subsession.round_number - 1],
            blur=player.session.config.get("blur", True),
            live_draw=player.session.config.get("live_draw", True),
            num_trials=C.NUM_PHASE_TRIALS[player.subsession.round_number - 1]
        )

    @staticmethod
    def live_method(player, data):
        # If the phase is complete the player needs to
        if is_phase_complete(player):
            return {
                player.id_in_group: dict(
                    event='continue',
                    phase_complete=True,
                )
            }
        
        trial = get_current_trial(player)

        # if the trial is complete, we need to move on
        # but if we are here we know the phase is not complete
        if trial.completed:
            return {
                player.id_in_group: dict(
                    event='continue',
                    phase_complete=False,
                )
            }
        drawing_player = is_drawer(player, trial)
        correct_stim = ""
        stim_list = get_stim_list(player, True)
        correct_stim = trial.stim
        if "event" in data:
            print("received event from ", player.id_in_group, data["event"])
            if data["event"] == "init":
                print("received init from ", player.id_in_group)
                if drawing_player and not trial.drawing.completed:
                    # start the drawing timer
                    if trial.drawing.start_timestamp == 0.0:
                        trial.drawing.start_timestamp = datetime.datetime.now().timestamp()
                    trial.drawing.drawing_time = datetime.datetime.now().timestamp() - trial.drawing.start_timestamp
                    print("drawing time: ", trial.drawing.drawing_time)
                    print("time left: ", C.DRAWING_TIME - trial.drawing.drawing_time)
                return {
                    player.id_in_group: dict(
                        event='init',
                        drawer=drawing_player,
                        # this allows recovery / in case of browser reload
                        drawing=base64.b64encode(trial.drawing.svg.encode('utf-8')).decode('utf-8'),
                        completed=trial.drawing.completed,
                        response_completed=trial.response.completed,
                        response_correct=trial.response.correct,
                        response=trial.response.response,
                        stims=stim_list,
                        correct_stim=correct_stim if drawing_player or trial.response.completed else '',
                        ready=player.ready,
                        trial_id=player.group.current_trial,
                        time_left=C.DRAWING_TIME - trial.drawing.drawing_time, # will be 120 at the start as Drawing.drawing_time starts at 0
                    )
                }
            elif data["event"] == "update":
                if drawing_player:
                    print("updating drawing for ", player.id_in_group)
                    trial.drawing.svg = base64.b64decode(data["drawing"]).decode('utf-8')
            elif data["event"] == "drawing_complete":
                if drawing_player:
                    trial.drawing.drawing_time = datetime.datetime.now().timestamp() - trial.drawing.start_timestamp
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
                            stims=stim_list,
                        )}
            elif data["event"] == "stimulus_selected": # just a click, not the "completed" event
                if not drawing_player:
                    print(f"received stimulus selection ({data['stim']}) from {player.id_in_group}")
                    trial.response.response = data["stim"]
                    
            elif data["event"] == "response_complete":
                if not drawing_player:
                    print(f"received response from {player.id_in_group}: response={data['response']}, correct_stim={correct_stim}")
                    trial.response.response = data["response"]
                    trial.response.correct = data["response"] == trial.stim
                    trial.response.completed = True
                    return {
                        0: dict(
                            event='show_response',
                            response=trial.response.response,
                            correct=trial.response.correct,
                            stims=stim_list,
                            correct_stim=correct_stim,
                            completed=True,
                        )
                    }
            elif data["event"] == "continue":
                # this is when both players have reviewed the response
                # and are ready to continue to the next trial
                # we have already checked earlier if the phase or trial is complete
                if trial.response.completed and trial.drawing.completed:
                    partner = get_partner(player)
                    player.ready = True
                    if partner.ready:
                        player.group.current_trial += 1
                        player.ready = False
                        partner.ready = False
                        trial.completed = True
                        return {
                            0: dict(
                                event='continue',
                                phase_complete=is_phase_complete(player),
                            )
                        }
                    else:
                        return {
                            player.id_in_group: dict(
                                event='continue_wait',
                                phase_complete=is_phase_complete(player),
                            )
                        }
            elif data["event"] == "get_remaining_time":
                if drawing_player:
                    # start the drawing timer (it should be started already, but just in case)
                    if trial.drawing.start_timestamp == 0.0:
                        trial.drawing.start_timestamp = datetime.datetime.now().timestamp()
                    trial.drawing.drawing_time = datetime.datetime.now().timestamp() - trial.drawing.start_timestamp
                return {
                    player.id_in_group: dict(
                        event='remaining_time',
                        time_left=C.DRAWING_TIME - trial.drawing.drawing_time,
                    )
                }


page_sequence = [
    ExperimentWelcome,
    PhaseInstructions,
    Waiting,
    # this page will repeat for the number of rounds in each phase
    Drawing,
    # PhaseComplete, # this is no longer needed
    PostExperimentSurvey,
    ExperimentThankYou,
]


# Define the custom export function to get the drawing and trial information
def custom_export(players):
    yield [
        "session",
        "group_id",  # pseudo group id
        "participant_1",
        "participant_2",
        "drawer",
        "responder",
        "phase",
        "trial",
        "stim",
        "concepts",
        "response",
        "correct",
        "response_completed",
        "drawing_completed",
        "drawing_time",
        "svg",
        "stim_order",
        # survey data
        "participant_1_age",
        "participant_1_gender",
        "participant_1_native_language",
        "participant_1_language_other",
        "participant_1_i_you",
        "participant_1_present_past",
        "participant_1_could_should",
        "participant_2_age",
        "participant_2_gender",
        "participant_2_native_language",
        "participant_2_language_other",
        "participant_2_i_you",
        "participant_2_present_past",
        "participant_2_could_should",
    ]

    trials = PictionaryTrial.filter()

    if not trials:
        return
    
    # get pseudo participant_1 and 2
    participant_1 = trials[0].drawer
    participant_2 = trials[0].responder
    # pseudo group id
    group_code = participant_1.participant.code + '_' + participant_2.participant.code

    for trial in trials:
        yield [
            trial.subsess.session.code if trial.subsess else "N/A",
            group_code,
            participant_1.participant.code,
            participant_2.participant.code,
            trial.drawer.participant.code,
            trial.responder.participant.code,
            trial.phase,
            trial.trial,
            trial.stim,
            trial.concepts,
            trial.response.response if trial.response else "N/A",
            trial.response.correct if trial.response else "N/A",
            trial.response.completed if trial.response else "N/A",
            trial.drawing.completed if trial.drawing else "N/A",
            trial.drawing.drawing_time if trial.drawing else "N/A",
            trial.drawing.svg if trial.drawing else "N/A",
            trial.group.stim_order if trial.group else "N/A",
            # survey data
            participant_1.age,
            participant_1.field_display('gender'),
            participant_1.native_language,
            participant_1.language_other,
            participant_1.i_you,
            participant_1.present_past,
            participant_1.could_should,
            participant_2.age,
            participant_2.field_display('gender'),
            participant_2.native_language,
            participant_2.language_other,
            participant_2.i_you,
            participant_2.present_past,
            participant_2.could_should,
        ]
