import hashlib
import uuid

import boto.ses as ses
import itsdangerous
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext


CONFIRMATION_PARAM = '__ctx'


def _send_mail(to, subject, body, email_format='text'):
    conn = ses.connect_to_region(
        'us-east-1',
        aws_access_key_id=settings.SES_ACCESS_ID,
        aws_secret_access_key=settings.SES_SECRET_KEY)
    print 'Sending email to %s' % to
    conn.send_email(
        source='mattbasta@gmail.com',
        subject=subject,
        body=body,
        to_addresses=to,
        format=email_format,
        return_path=settings.ADMINS[0][1]
    )


signer = itsdangerous.TimestampSigner(settings.SECRET_KEY)


def send_confirmation_email(user, subject, description, url, email=None):
    email = email or user.email
    if not url.startswith('/'):
        url = '/%s' % url
    if '?' in url:
        signed_url = '%s&' % url
    else:
        signed_url = '%s?' % url

    token = hashlib.sha1(url).hexdigest()
    signed_url += '%s=%s' % (CONFIRMATION_PARAM, signer.sign(token))

    body = ugettext('''{description}

To confirm this request, visit the link below.

https://host.podmaster.io{url}
''').format(username=user.username, description=description, url=signed_url)
    return send_notification_email(user, subject, body, email)


def send_notification_email(user, subject, description, email=None):
    email = email or user.email
    body = ugettext('''Hello {username},

{description}

Thanks,
Podmaster Host
    ''').format(username=user.username, description=description)
    return _send_mail(email, subject, body)


def validate_confirmation(req, max_age=settings.EMAIL_CONFIRMATION_MAX_AGE):
    full_path = req.get_full_path()
    param_loc = full_path.index(CONFIRMATION_PARAM)
    trimmed_path = full_path[:param_loc - 1]
    signature = signer.unsign(req.GET.get(CONFIRMATION_PARAM), max_age=max_age)
    return hashlib.sha1(trimmed_path).hexdigest() == signature


def request_must_be_confirmed(view):
    def wrap(*args, **kwargs):
        if not validate_confirmation(args[0]):
            return HttpResponseBadRequest()
        return view(*args, **kwargs)
    return wrap
