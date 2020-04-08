from django.shortcuts import render, redirect, Http404
from django.middleware import csrf
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import Peer, Session
from .apps import Var

import datetime

def _utils_check_session_time(request, peer, sessId):
    print("checking session info")
    sess = peer.sess
    if sess.sessId != sessId:
        return render(request, "LiveStreamApp/error.html", {'error':"Not a Valid Session. Kindly avoid tresspassing into other webinar","which":"register"})

    time_now = datetime.datetime.now()
    start_time = sess.startTime
    print(time_now, start_time)
    end_time = start_time + datetime.timedelta(minutes=sess.interval)
    # print(time_now.replace(tzinfo=None),start_time.replace(tzinfo=None), end_time.replace(tzinfo=None))
    if time_now.replace(tzinfo=None) > end_time.replace(tzinfo=None):
        return render(request, "LiveStreamApp/error.html", {"error":"Session has expired, Sorry :'("})
        
    elif time_now.replace(tzinfo=None) < start_time.replace(tzinfo=None):
        return render(request, "LiveStreamApp/error.html", {"error":"Session Yet to Start, Have Patience :)","start_time":start_time})
    else:
        if peer.who == "Teacher":
            return render(request, "LiveStreamApp/host.html", {"sess":peer.sess.sessId, "id":peer.id})
        else:
            return render(request, "LiveStreamApp/peer.html", {"sess":peer.sess.sessId, "id":peer.id})

def http404(request, error="error"):
    return render(request, "LiveStreamApp/error.html", {"error" : error})


def host(request, name, id):
    print("getting host")
    peer = get_object_or_404(Peer, id=id)
    if peer.who == "Student":
        return http404(request, "This is Only for HOST.. FallBack!! :|")
    return _utils_check_session_time(request, peer, name)
        
def hostlogin(request, name): 
    csrf_token = csrf.get_token(request)
    if request.method=="POST":
        data = (request.POST)
        user = data["username"]
        mob = data["mobile"]
        try:
            print("verifying the session id ", name)
            sessId = Session.objects.get(pk=name)
            peer = Peer()
            peer.id = Peer.objects.all().count()+1
            peer.sess = sessId
            peer.name = user
            peer.mob = mob
            peer.who = "Teacher"
        except ObjectDoesNotExist():
            raise Http404()
        print(peer.id)
        peer.save()
        return redirect("host", name = name, id = peer.id)
    return render_to_response('LiveStreamApp/hostlogin.html', {"csrf_token":csrf_token})

def peer(request, name, id):
    peer = get_object_or_404(Peer, id=id)
    if peer.who == "Teacher":
        return http404(request, "Sorry Host, This is Only for Students.. Kindly FallBack!! :|")
    return _utils_check_session_time(request, peer, name)


def peerlogin(request, name):
    csrf_token = csrf.get_token(request)
    if request.method=="POST":
        data = (request.POST)
        user = data["username"]
        _class = data["class"]
        section = data["section"]
        mob = data["mobile"]
        try:
            print("verifying the session id ", name)
            sessId = Session.objects.get(pk=name)
            peer = Peer()
            peer.sess = sessId
            peer.id = Peer.objects.all().count()+1
            peer.name = user
            peer.mob = mob
            peer.clss = _class
            peer.section = section
            peer.who = "Student"
        except:
            raise Http404
        peer.save()
        return redirect("peer", name = name, id = peer.id )
    return render_to_response("LiveStreamApp/peerlogin.html", {"csrf_token":csrf_token})



def webinar(request):
    return render_to_response("LiveStreamApp/base.html")

