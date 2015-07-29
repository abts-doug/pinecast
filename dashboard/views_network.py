from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext, ugettext_lazy
from django.views.decorators.http import require_POST

from accounts.models import Network
from podcasts.models import Podcast
from podmaster.helpers import reverse
from views import _pmrender, signer


@login_required
def network_dashboard(req, network_id):
    net = get_object_or_404(Network, deactivated=False, id=network_id, members__in=[req.user])

    ame = ugettext('No user with that email address was found') if req.GET.get('add_member_error') == 'dne' else None
    added_member = req.GET.get('added_member', 'false') == 'true'
    return _pmrender(req,
                     'dashboard/network/netdash.html',
                     {'network': net,
                      'add_member_error': ame,
                      'add_member_success': added_member})


@login_required
def network_add_show(req, network_id):
    net = get_object_or_404(Network, deactivated=False, id=network_id, members__in=[req.user])
    if req.POST:
        slug = req.POST.get('slug')
        try:
            pod = Podcast.objects.get(slug=slug)
        except Podcast.DoesNotExist:
            return _pmrender(req, 'dashboard/network/add_show.html', {'network': net, 'error': ugettext('No podcast with the slug "%s" was found') % slug})
        else:
            if pod.owner != req.user:
                return _pmrender(req, 'dashboard/network/add_show.html', {'network': net, 'error': ugettext('You must be the owner of a podcast to add it to a network')})
            pod.networks.add(net)
            pod.save()
        return redirect('network_dashboard', network_id=net.id)
            
    return _pmrender(req, 'dashboard/network/add_show.html', {'network': net})


@login_required
@require_POST
def network_add_member(req, network_id):
    net = get_object_or_404(Network, deactivated=False, id=network_id, members__in=[req.user])

    try:
        user = User.objects.get(email=req.POST.get('email'))
    except User.DoesNotExist:
        return redirect(reverse('network_dashboard', network_id=network_id) + '?add_member_error=dne#tab-members')

    net.members.add(user)
    net.save()

    return redirect(reverse('network_dashboard', network_id=net.id) + '?added_member=true#tab-members')


@login_required
def network_edit(req, network_id):
    net = get_object_or_404(Network, deactivated=False, id=network_id, members__in=[req.user])
    
    if not req.POST:
        return _pmrender(req, 'dashboard/network/edit.html', {'network': net})

    try:
        net.name = req.POST.get('name')
        net.image_url = signer.unsign(req.POST.get('image-url'))
        net.save()
    except Exception:
        return _pmrender(req,
                         'dashboard/network/edit.html',
                         {'network': net, 'error': ugettext('Error while saving network details')})

    return redirect('network_dashboard', network_id=net.id)


@login_required
def network_deactivate(req, network_id):
    net = get_object_or_404(Network, deactivated=False, id=network_id, members__in=[req.user])
    
    if not req.POST:
        return _pmrender(req, 'dashboard/network/deactivate.html', {'network': net})

    if req.POST.get('confirm') != 'doit':
        return redirect('dashboard')

    net.deactivated = True
    net.save()

    return redirect('dashboard')
