from os import environ

SESSION_CONFIGS = [
    dict(
        name='pictionary_live_drawing',
        app_sequence=[
            'pictionary',
        ],
        num_demo_participants=2,
        live_draw=True,
        blur=True,
    ),
    dict(
        name='pictionary_live_drawing_no_blur',
        app_sequence=[
            'pictionary',
        ],
        num_demo_participants=2,
        live_draw=True,
        blur=False,
    ),
    dict(
        name='pictionary_wait_for_complete',
        app_sequence=[
            'pictionary',
        ],
        num_demo_participants=2,
        live_draw=False,
        blur=False,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS: list[str] = []
SESSION_FIELDS: list[str] = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

SECRET_KEY = '1705882164517'

DEBUG = True