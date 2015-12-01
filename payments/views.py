from django.contrib.auth.decorators import login_required

from accounts.models import UserSettings
from dashboard.views import _pmrender


@login_required
def upgrade(req):
    us = UserSettings.get_from_user(req.user)
    customer = us.get_stripe_customer()

    ctx = {
        'stripe_customer': customer,
    }

    return _pmrender(req, 'payments/upgrade.html', ctx)
