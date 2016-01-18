import stripe
from django.conf import settings


stripe.api_key = settings.STRIPE_API_KEY

__all__ = ['stripe']
