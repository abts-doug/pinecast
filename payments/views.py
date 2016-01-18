from django.contrib.auth.decorators import login_required

from accounts.models import UserSettings
from dashboard.views import _pmrender
from pinecast.helpers import json_response, reverse


@login_required
def upgrade(req):
    us = UserSettings.get_from_user(req.user)
    customer = us.get_stripe_customer()

    ctx = {
        'stripe_customer': customer,
    }

    return _pmrender(req, 'payments/main.html', ctx)


@login_required
@json_response
def set_payment_method(req):
    us = UserSettings.get_from_user(req.user)
    customer = us.get_stripe_customer()
    if customer:
        customer.source = req.POST.get('token')
        customer.save()
    else:
        us.create_stripe_customer(req.POST.get('token'))

    return {'success': True, 'id': us.stripe_customer_id}
