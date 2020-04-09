from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from django.shortcuts import redirect
from channels.db import database_sync_to_async
from django.shortcuts import Http404
from django.core.exceptions import ObjectDoesNotExist

# from .apps import Var
from .models import Session, Peer

import datetime as dt
import json
import pickle

class consumer(AsyncConsumer):
    name = ""
    User = ""
    groupName = ""
    sessId = None
    who = ""
    peer = None
    isActiveHost=False
    def exception_handler(self, error):
        print(error)
        if self.sessId and self.isActiveHost == True:
            if self.sessId.isActive == True:
                self.sessId.isActive = False
                self.sessId.save()
        self.peer.logout = dt.datetime.now()
        self.peer.save()
        raise StopConsumer()

    async def websocket_connect(self, event):
        try:
            await self.send({
                "type" : "websocket.accept",
            })
            self.name = self.scope['url_route']['kwargs']['name']
            self.User = self.scope['url_route']['kwargs']['identity']
            who_id = self.User.split("_")
            print(self.name, who_id)
            self.who = who_id[0]
            self.peer = Peer.objects.get(id=who_id[1])
            self.groupName = self.name+"_"+self.who
            self.sessId = Session.objects.get(pk=self.name)
            if self.who == "host":
                if self.sessId.isActive == True:
                    self.send({
                        "type" : "websocket.send",
                        "message" : "There is one active Host for this Session Id, You are not allowed"
                    })
                    print("Disconnectinggg not valid host")
                    self.send({
                        "type" : "websocket.disconnect",
                    })
                    return
                print("is a valid host")
                
                self.sessId.isActive = True
                self.isActiveHost = True
                self.sessId.save()
                await self.channel_layer.group_send(
                        self.name+"_peer",
                        {
                            'type' : 'websocket.broadcast',
                            'what' : 'open',
                            'message': "we got a Host {}..".format(self.User),
                            'user' : self.User,
                            'userId' : self.peer.id
                        }
                    )
                
            if self.who == "peer":
                if self.sessId.isActive == True:
                    await self.channel_layer.group_send(
                        self.name+"_host",
                        {
                            'type' : 'websocket.broadcast',
                            'what' : 'open',
                            'message': "we got a new user {}..".format(self.User),
                            'user' : self.User,
                            'userId' : self.peer.id
                        }
                    )
                else:
                    self.send({
                        "type" : "websocket.send",
                        "message": "Session is Not Live/Expired"
                    })
                    print("Disconnectinggg session not live")
                    self.send({
                        "type" : "websocket.disconnect"
                    })
                    return
            
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "recv" : "open",
                    "userid" : self.peer.id,
                    "user" : self.User,
                    "message" : "Sockets connected"
                })
            })

            await self.channel_layer.group_add(
                self.groupName,
                self.channel_name
            )
            await self.channel_layer.group_add(
                self.name+"_"+"all",
                self.channel_name
            )
        except Exception as error:
            print("exception occured,,..", error)
            self.exception_handler(error)
            # raise StopConsumer()

    async def websocket_receive(self, event):
        # print("recieving.. ", event)
        try:
            data = json.loads(event["text"])
            if "offer" in data:
                # print("recieved offer..broadcasting to all peers...")
                await self.channel_layer.group_send(
                    self.name+"_peer",
                    {
                    "type": "websocket.broadcast",
                    "what":"offer",
                    "message" :data["offer"],
                    "for" : data["for"],
                    "isLive" : data["isLive"]
                    }
                )
                print("offer broadcasted to peers...")

            elif "answer" in  data:
                # Var.answered = True
                # Var.Answer = data["answer"]
                # print("recived answer.. broadcasting to host")
                await self.channel_layer.group_send(
                    self.name+"_host",
                    {
                    "type" : "websocket.broadcast",
                    "what" : "answer",
                    "message" : data["answer"],
                    "by" : data["by"]
                })
            elif "candidate" in data:
                # print("recieved ICECandidate from ", data["who"])
                # print(data["candidate"])
                if data["who"] == "peer":
                    await self.channel_layer.group_send(
                        self.name+"_host",
                        {
                            "type":"websocket.broadcast",
                            "what":"iceCand",
                            "message": data["candidate"],
                            "by" : data["by"]
                        }
                    )
                else:
                    await self.channel_layer.group_send(
                        self.name+"_peer",
                        {
                            "type":"websocket.broadcast",
                            "what":"iceCand",
                            "for":data["for"],
                            "message":data["candidate"]
                        }
                    )
            elif "file" in data:
                pass
            elif "msg" in data:
                pass
            else:
                pass
        except Exception as error: 
            print("exception occured,,..", error)
            self.exception_handler(error)
            raise StopConsumer()


    async def websocket_disconnect(self, event):
        self.peer.logout = dt.datetime.now()
        self.peer.save()
        try:
            if self.who=="host":
                print("Setting session False")
                self.sessId.isActive = False
                self.sessId.save()
            else:
                await self.channel_layer.group_send(
                    self.name+"_host",
                    {
                    "type" : "websocket.broadcast",
                    "what" : "close",
                    "user" : self.User,
                    "message" : "{} Disconnected".format(self.who)
                    }
                )
            await self.send({
                "type" : "websocket.close"
            })
            raise StopConsumer
        except Exception as error:
            self.exception_handler(error)
            raise StopConsumer()

    async def websocket_broadcast(self, event):
        # print(event)
        try:
            what = event["what"]
            # print(event["message"])
            # print("Broadcasting... ", what)
            if what == "open":    
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "open_broadcast" : event['message'],
                        "recv" : "open_broadcast",
                        "userId" : event["userId"],
                        "user" : event["user"],
                        "message": "open_user"
                    })
                })
            elif what == "close":
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "close_broadcast": event['message'],
                        "recv" : "close_broadcast",
                        "user" : event["user"],
                        "message":"close_user"
                    })
                })
            elif what == "offer":
                if self.User == event["for"]:
                    await self.send({
                        "type" : "websocket.send",
                        "text" : json.dumps({
                            "recv" : "offer",
                            "offer": event['message'],
                            "message":"recieved Offer",
                            "isLive" : event["isLive"]
                        })
                    })
                    
            elif what == "answer":
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "recv" : "answer",
                        "answer" : event['message'],
                        "by" : event["by"],
                        'message' : "recieved Answer"
                    })
                })
            elif what == "iceCand":
                if "for" in event:
                    if event["for"] == self.User:
                        await self.send({
                            "type" : "websocket.send",
                            "text" : json.dumps({
                                "recv" : "iceCand",
                                "candidate": event["message"],
                                "for" : event["for"],
                                "message":"iceCandidates recieved"
                            })
                        })
                elif "by" in event:
                    await self.send({
                        "type" : "websocket.send",
                        "text" : json.dumps({
                            "recv" : "iceCand",
                            "candidate": event["message"],
                            "by" : event["by"],
                            "message":"iceCandidates recieved"
                        })
                    })
        except Exception as error:
            self.exception_handler(error)
            raise StopConsumer()