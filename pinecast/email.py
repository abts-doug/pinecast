import hashlib
import uuid

import itsdangerous
from boto3.session import Session
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import ugettext

from .signatures import signer


CONFIRMATION_PARAM = '__ctx'


def _send_mail(to, subject, body, email_format='Text'):
    session = Session(aws_access_key_id=settings.SES_ACCESS_ID,
                      aws_secret_access_key=settings.SES_SECRET_KEY,
                      region_name='us-east-1')
    conn = session.client('ses')
    print 'Sending email to %s' % to
    conn.send_email(
        Source='mattbasta@gmail.com',
        Destination={'ToAddresses': [to]},
        Message={
            'Subject': {
                'Data': subject,
            },
            'Body': {
                email_format: {
                    'Data': body,
                },
            },
        },
        ReplyToAddresses=[settings.SUPPORT_EMAIL],
        ReturnPath=settings.ADMINS[0][1]
    )


def send_confirmation_email(user, subject, description, url, email=None):
    email = email or user.email
    signed_url = get_signed_url(url)
    body = ugettext('''{description}

To confirm this request, visit the link below.

https://pinecast.com{url}
''').format(username=user.username, description=description, url=signed_url)
    return send_notification_email(user, subject, body, email)


def send_notification_email(user, subject, description, email=None):
    email = email or user.email
    body = ugettext('''Hello {username},

{description}

Thanks,
The Pinecast Team
    ''').format(username=user.username, description=description)
    return _send_mail(email, subject, body)


def validate_confirmation(req, max_age=settings.EMAIL_CONFIRMATION_MAX_AGE):
    full_path = req.get_full_path()
    param_loc = full_path.index(CONFIRMATION_PARAM)
    trimmed_path = full_path[:param_loc - 1]
    signed = req.GET.get(CONFIRMATION_PARAM)
    try:
        signature = signer.unsign(signed, max_age=max_age)
        return hashlib.sha1(trimmed_path).hexdigest() == signature
    except itsdangerous.BadTimeSignature:
        return False


def request_must_be_confirmed(view):
    def wrap(*args, **kwargs):
        if not validate_confirmation(args[0]):
            return get_expired_page(args[0])
        return view(*args, **kwargs)
    return wrap


def get_signed_url(url):
    if not url.startswith('/'):
        url = '/%s' % url
    if '?' in url:
        signed_url = '%s&' % url
    else:
        signed_url = '%s?' % url

    token = hashlib.sha1(url).hexdigest()
    signed_url += '%s=%s' % (CONFIRMATION_PARAM, signer.sign(token))
    return signed_url


def get_expired_page(req):
    return HttpResponseBadRequest(render(req, 'bad_signature.html'))
