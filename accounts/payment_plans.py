from django.utils.translation import ugettext_lazy

PLAN_DEMO = 0
PLAN_STARTER = 1
PLAN_PRO = 2
PLAN_ULTIMATE = 3


PLANS = (
    (PLAN_DEMO, ugettext_lazy('Demo')),
    (PLAN_STARTER, ugettext_lazy('Starter')),
    (PLAN_PRO, ugettext_lazy('Pro')),
    (PLAN_ULTIMATE, ugettext_lazy('Ultimate')),
)
