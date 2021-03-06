import re
from urllib import quote as urlencode

import pytz
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext
from django.views.decorators.http import require_POST

from .models import BetaRequest, UserSettings
from dashboard.views import _pmrender
from pinecast.email import get_expired_page, get_signed_url, request_must_be_confirmed, send_confirmation_email, send_notification_email
from pinecast.helpers import reverse, tz_offset
from pinecast.signatures import signer


def home(req):
    if not req.user.is_anonymous():
        return redirect('dashboard')

    return redirect('https://www.pinecast.com/')


def login_page(req):
    if not req.user.is_anonymous():
        return redirect('dashboard')

    ctx = {}
    if req.GET.get('signup_success'):
        ctx['success'] = ugettext('Your account was created successfully. Login below.')

    if not req.POST:
        return render(req, 'login.html', ctx)

    try:
        user = User.objects.get(email=req.POST.get('email'))
        password = req.POST.get('password')
    except User.DoesNotExist:
        user = None

    if (user and
        user.is_active and
        user.check_password(password)):
        login(req, authenticate(username=user.username, password=password))
        return redirect('dashboard')

    ctx['error'] = ugettext('Invalid credentials')
    return render(req, 'login.html', ctx)


def forgot_password(req):
    if not req.user.is_anonymous():
        return redirect('dashboard')

    if not req.POST:
        return render(req, 'forgot_password.html')

    try:
        user = User.objects.get(email=req.POST.get('email'))
    except User.DoesNotExist:
        user = None

    if user and user.is_active:
        send_confirmation_email(
            user,
            ugettext('[Pinecast] Password reset'),
            ugettext('''
We received a request to reset the password for your Pinecast account. If you
do not want to reset your password, please ignore this email.
'''),
            reverse('forgot_password_finalize') + '?email=%s' % urlencode(user.email))
        return render(req, 'forgot_password_success.html')
    return render(req, 'forgot_password.html', {'error': ugettext("We don't recognize that email address.")})


@request_must_be_confirmed
def forgot_password_finalize(req):
    if not req.user.is_anonymous():
        return redirect('dashboard')

    email = req.GET.get('email')
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return redirect('login')

    ctx = {'email': email,
           'signature': signer.sign(email),
           'error': req.GET.get('error')}

    return render(req, 'forgot_password_finalize.html', ctx)


@require_POST
def forgot_password_finish(req):
    if not req.user.is_anonymous():
        return redirect('dashboard')

    # Protection against the forces of evil
    sig = req.POST.get('__sig')
    email = req.POST.get('email')
    try:
        h = signer.unsign(sig, max_age=1800)
        if h != email:
            raise Exception()
    except Exception:
        return get_expired_page(req)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return redirect('login')

    passwd = req.POST.get('password')
    if passwd != req.POST.get('confirm'):
        err = ugettext("You didn't type the same password twice.")
        return redirect(
            get_signed_url(
                reverse('forgot_password_finalize') +
                '?email=%s&error=%s' % (
                    urlencode(email),
                    urlencode(err))
            )
        )

    user.set_password(passwd)
    user.save()

    return redirect(reverse('login') + '?success=resetpassword')


@login_required
def user_settings_page(req):
    return _pmrender(req, 'account/settings.html',
                     {'success': req.GET.get('success'), 'error': req.GET.get('error')})

@login_required
@require_POST
def user_settings_page_savetz(req):
    us = UserSettings.get_from_user(req.user)
    us.tz_offset = tz_offset(req.POST.get('timezone'))
    us.save()
    return redirect(reverse('user_settings') + '?success=tz')

@login_required
@require_POST
def user_settings_page_changeemail(req):
    if User.objects.filter(email=req.POST.get('new_email')).count():
        return redirect(reverse('user_settings') + '?error=eae')
    send_confirmation_email(
        req.user,
        ugettext('[Pinecast] Email change confirmation'),
        ugettext('''
Someone requested a change to your email address on Pinecast. This email is
to verify that you own the email address provided.
'''),
        reverse('user_settings_change_email_finalize') + '?user=%s&email=%s' % (
            urlencode(req.user.id), urlencode(req.POST.get('new_email'))),
        req.POST.get('new_email')
    )
    return redirect(reverse('user_settings') + '?success=em')

@login_required
@require_POST
def user_settings_page_changepassword(req):
    if req.POST.get('new_password') != req.POST.get('confirm_password'):
        return redirect(reverse('user_settings') + '?error=pwc')
    if not req.user.check_password(req.POST.get('old_password')):
        return redirect(reverse('user_settings') + '?error=pwo')
    if len(req.POST.get('new_password')) < 8:
        return redirect(reverse('user_settings') + '?error=pwl')

    req.user.set_password(req.POST.get('new_password'))
    req.user.save()

    send_notification_email(
        req.user,
        ugettext('[Pinecast] Password changed'),
        ugettext('''
Your Pinecast password has been updated. If you did not request this change,
please contact Pinecast support as soon as possible at
support@pinecast.zendesk.com.
''')
    )
    return redirect(reverse('login'))

@login_required
@request_must_be_confirmed
def user_settings_page_changeemail_finalize(req):
    user = get_object_or_404(User, id=req.GET.get('user'))
    user.email = req.GET.get('email')
    user.save()
    return redirect(reverse('user_settings') + '?success=emf')
