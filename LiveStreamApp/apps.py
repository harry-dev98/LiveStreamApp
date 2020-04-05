from django.apps import AppConfig


class LivestreamappConfig(AppConfig):
    name = 'LiveStreamApp'

class Var():
    Offer = dict()
    Answer = dict()
    answered = False
    offered = False
    offerICE = []
    answerICE = []
    users = dict()