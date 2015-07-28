from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.translation import ugettext

from .models import BetaRequest


def home(req):
    if not req.user.is_anonymous():
        return redirect('dashboard')

    return redirect('beta_signup')


def login_page(req):
    if not req.user.is_anonymous():
        return redirect('dashboard')

    if not req.POST:
        return render(req, 'login.html')

    try:
        user = User.objects.get(email=req.POST.get('email'))
        password = req.POST.get('password')
    except User.DoesNotExist:
        pass

    if (user and
        user.is_active and
        user.check_password(password)):
        login(req, authenticate(username=user.username, password=password))
        return redirect('dashboard')
    return render(req, 'login.html', {'error': ugettext('Invalid credentials')})


def private_beta_signup(req):
    if not req.POST:
        return render(req, 'pb_signup.html', {'types': BetaRequest.PODCASTER_TYPE})

    request = BetaRequest(
        email=req.POST.get('email'),
        podcaster_type=req.POST.get('type')
    )
    request.save()
    
    return render(req, 'pb_signup_done.html')
