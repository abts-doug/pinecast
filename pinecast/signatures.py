import itsdangerous
from django.conf import settings

signer = itsdangerous.TimestampSigner(settings.SECRET_KEY)
