from otree.api import BaseConstants, BaseSubsession, BaseGroup, BasePlayer, models, Page

doc = """
Showing other players' decisions from previous rounds
"""

class C(BaseConstants):
    NAME_IN_URL = 'pictionary'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 5


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    import random

    subsession.group_randomly()

    # for demo purposes we just generate random data.
    # of course in a real game, there would be a formfield where a user
    # enters their contribution
    for player in subsession.get_players():
        player.contribution = random.randint(0, 99)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    contribution = models.IntegerField()


def get_partner(player: Player):
    return player.get_others_in_group()[0]


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
        )


page_sequence = [Drawing]