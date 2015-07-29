from django.utils.translation import ugettext_lazy

PLAN_DEMO = 0
PLAN_STARTER = 1
PLAN_PRO = 2
PLAN_ULTIMATE = 3
PLAN_COMMUNITY = 4

PLANS = (
    (PLAN_DEMO, ugettext_lazy('Demo')),
    (PLAN_STARTER, ugettext_lazy('Starter')),
    (PLAN_PRO, ugettext_lazy('Pro')),
    (PLAN_ULTIMATE, ugettext_lazy('Ultimate')),
    (PLAN_COMMUNITY, ugettext_lazy('Community')),
)
PLANS_MAP = {x: y for x, y in PLANS}

PLAN_RANKS = {
    PLAN_DEMO: 0,
    PLAN_STARTER: 1,
    PLAN_COMMUNITY: 1,
    PLAN_PRO: 2,
    PLAN_ULTIMATE: 3,
}

FEATURE_MIN_COMMENT_BOX = PLAN_PRO
FEATURE_MIN_PLAYER = PLAN_STARTER
FEATURE_MIN_IMPORTER = PLAN_STARTER

PLANS_RAW = {
    'PLAN_DEMO': PLAN_DEMO,
    'PLAN_STARTER': PLAN_STARTER,
    'PLAN_PRO': PLAN_PRO,
    'PLAN_ULTIMATE': PLAN_ULTIMATE,
    'PLAN_COMMUNITY': PLAN_COMMUNITY,

    'FEATURE_MIN_COMMENT_BOX': FEATURE_MIN_COMMENT_BOX,
    'FEATURE_MIN_PLAYER': FEATURE_MIN_PLAYER,
    'FEATURE_MIN_IMPORTER': FEATURE_MIN_IMPORTER,
}

def minimum(plan_to_compare, minimum_plan):
    return PLAN_RANKS[plan_to_compare] >= PLAN_RANKS[minimum_plan]
