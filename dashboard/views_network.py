from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy
from django.views.decorators.http import require_POST

from accounts.models import Network
from podcasts.models import Podcast
from podmaster.helpers import reverse
from views import _pmrender


NET_MEMBER_ERRORS = {
    'dne': 'No user with that email address was found',
}


@login_required
def network_dashboard(req, network_id):
    net = get_object_or_404(Network, id=network_id, members__in=[req.user])

    ame = NET_MEMBER_ERRORS.get(req.GET.get('add_member_error'), None)
    added_member = req.GET.get('added_member', 'false') == 'true'
    return _pmrender(req,
                     'dashboard/network/netdash.html',
                     {'network': net,
                      'add_member_error': ame,
                      'add_member_success': added_member})


@login_required
def network_add_show(req, network_id):
    net = get_object_or_404(Network, id=network_id, members__in=[req.user])
    if req.POST:
        slug = req.POST.get('slug')
        try:
            pod = Podcast.objects.get(slug=slug)
        except Podcast.DoesNotExist:
            return _pmrender(req, 'dashboard/network/add_show.html', {'network': net, 'error': 'No podcast with the slug "%s" was found' % slug})
        else:
            pod.networks.add(net)
            pod.save()
            net.members.add(pod.owner)
            net.save()
        return redirect('network_dashboard', network_id=net.id)
            
    return _pmrender(req, 'dashboard/network/add_show.html', {'network': net})


@login_required
@require_POST
def network_add_member(req, network_id):
    net = get_object_or_404(Network, id=network_id, members__in=[req.user])

    try:
        user = User.objects.get(email=req.POST.get('email'))
    except User.DoesNotExist:
        return redirect(reverse('network_dashboard', network_id=network_id) + '?add_member_error=dne#tab-members')

    net.members.add(user)
    net.save()

    return redirect(reverse('network_dashboard', network_id=net.id) + '?added_member=true#tab-members')
