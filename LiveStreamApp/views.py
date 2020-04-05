from django.shortcuts import render

from django.shortcuts import render_to_response

# Create your views here.
def host(request, name):
    return render_to_response("LiveStreamApp/host.html", { 'sess':name })

def peer(request, name):
    return render_to_response("LiveStreamApp/peer.html", { 'sess':name })

def webinar(request):
    return render_to_response("LiveStreamApp/base.html")