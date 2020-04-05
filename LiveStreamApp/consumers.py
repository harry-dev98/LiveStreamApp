from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from django.shortcuts import redirect
from channels.db import database_sync_to_async

from .apps import Var
from .models import Session

import json
import pickle

class consumer(AsyncConsumer):
    name = ""
    User = ""
    groupName = ""
    sessId = None
    who = ""
    async def getSessId(self):
        try:
            print("verifying the session id ", self.name)
            self.sessId =await database_sync_to_async(Session.objects.get)(pk=self.name)
            
        except Session.DoesNotExist:
            await self.send({
            "type" : "websocket.close"
            })
            raise StopConsumer
        
    async def websocket_connect(self, event):
        await self.send({
            "type" : "websocket.accept",
        })
        self.name = self.scope['url_route']['kwargs']['name']
        self.who = self.scope['url_route']['kwargs']['who']
        await self.getSessId()
        if self.sessId == None:
            return

        if self.who == "host":
            if self.sessId.isActive == True:
                self.send({
                    "type" : "websocket.send",
                    "message" : "There is one active Host for this Session Id, You are not allowed"
                })
                self.send({
                    "type" : "websocket.close",
                })
                return
            self.sessId.isActive = True
            self.sessId.save()

        self.groupName = self.name+"_"+self.who
        count = len(Var.users)

        self.User = "{}_id_{}".format(self.who, count+1)
        
        Var.users[self.User] = count+1
        print("connection requested", event)
        await self.channel_layer.group_add(
            self.groupName,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.name+"_"+"all",
            self.channel_name
        )
        await self.send({
            "type" : "websocket.send",
            "text" : json.dumps({
                "recv" : "open",
                "userid" : Var.users[self.User],
                "user" : self.User,
                "message" : "Sockets connected"
            })
        })

        if self.who == "peer":
            if self.sessId.isActive == True:
                await self.channel_layer.group_send(
                    self.name+"_host",
                    {
                        'type' : 'websocket.broadcast',
                        'what' : 'open',
                        'message': "we got a new user {}..".format(self.User),
                        'user' : self.User,
                        'userId' : Var.users[self.User]
                    }
                )
            else:
                self.send({
                    "type" : "websocket.send",
                    "message": "Session is Not Live/Expired"
                })
                self.send({
                    "type" : "websocket.close"
                })

    async def websocket_receive(self, event):
        # print("recieving.. ", event)
        data = json.loads(event["text"])
        if "offer" in data:
            print("recieved offer..broadcasting to all peers...")
            Var.offered = True
            Var.offer = data["offer"]
            await self.channel_layer.group_send(
                self.name+"_peer",
                {
                "type": "websocket.broadcast",
                "what":"offer",
                "offer" :data["offer"],
                "for" : data["for"]
                }
            )
            print("offer broadcasted to peers...")

        elif "answer" in  data:
            Var.answered = True
            Var.Answer = data["answer"]
            print("recived answer.. broadcasting to host")
            await self.channel_layer.group_send(
                self.name+"_host",
                {
                "type" : "websocket.broadcast",
                "what" : "answer",
                "message" : data["answer"],
                "by" : data["by"]
            })
        elif "candidate" in data:
            print("recieved ICECandidate from ", data["who"])
            if data["who"] == "peer":
                await self.channel_layer.group_send(
                    self.name+"_host",
                    {
                        "type":"websocket.broadcast",
                        "what":"iceCand",
                        "message":data["candidate"],
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

    async def websocket_disconnect(self, event):
        if self.who=="host":
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


    async def websocket_broadcast(self, event):
        what = event["what"]
        print("Broadcasting... ", what)
        message = event["message"]
        if what == "open":    
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "open_broadcast" : message,
                    "recv" : "open_broadcast",
                    "userId" : event["userId"],
                    "user" : event["user"],
                    "message":message
                })
            })
        elif what == "close":
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "close_broadcast": message,
                    "recv" : "close_broadcast",
                    "user" : event["user"],
                    "message":message
                })
            })
        elif what == "offer":
            if self.User == event["for"]:
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "recv" : "offer",
                        "offer": message,
                        "message":"recieved Offer"
                    })
                })
                
        elif what == "answer":
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "recv" : "answer",
                    "answer" : message,
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
                            "candidate": message,
                            "for" : event["for"],
                            "message":"iceCandidates recieved"
                        })
                    })
            elif "by" in event:
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "recv" : "iceCand",
                        "candidate": message,
                        "by" : event["by"],
                        "message":"iceCandidates recieved"
                    })
                })