from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from django.shortcuts import redirect
from channels.db import database_sync_to_async

from .apps import Var

import json
import pickle



class consumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.name = self.scope['url_route']['kwargs']['name']
        self.who = self.scope['url_route']['kwargs']['who']
        print("connection requested", event)
        self.groupName = self.name+"_"+self.who
        
        await self.channel_layer.group_add(
            self.groupName,
            self.channel_name
        )

        await self.channel_layer.group_add(
            self.name+"_"+"all",
            self.channel_name
        )

        await self.send({
            "type": "websocket.accept"
        })
        await self.channel_layer.group_send(
            self.name+"_"+"all",
            {
                'type' : 'websocket.broadcast',
                'what' : 'open',
                'who' : self.who,
                'message': "we got a new {}..".format(self.who)
            }
        )

    async def websocket_receive(self, event):
        data = json.loads(event["text"])
        print("recieving.. ",data)
        if "offer" in data:
            print("recieved offer..broadcasting to all peers...")
            Var.offered = True
            Var.offer = data["offer"]
            await self.channel_layer.group_send(
                self.name+"_"+"peer",
                {
                "type": "websocket.broadcast",
                "what":"offer",
                "message" :data["offer"]
                }
            )
            print("offer broadcasted to peers...")

        elif "answer" in  data:
            Var.answered = True
            Var.Answer = data["answer"]
            print("recived answer.. broadcasting to host")
            await self.channel_layer.group_send(
                self.name+"_"+"host",
                {
                "type" : "websocket.broadcast",
                "what" : "answer",
                "message" : data["answer"]
            })

        
        elif "candidate" in data:
            print("recieved ICECandidate from ", data["who"])
            if data["who"] == "peer":
                await self.channel_layer.group_send(
                    self.name+"_host",
                    {
                        "type":"websocket.broadcast",
                        "what":"iceCand",
                        "message":data["candidate"]
                    }
                )
            else:
                await self.channel_layer.group_send(
                    self.name+"_peer",
                    {
                        "type":"websocket.broadcast",
                        "what":"iceCand",
                        "message":data["candidate"]
                    }
                )   

    async def websocket_disconnect(self, event):
        await self.send({
            "type" : "websocket.close"
        })
        await self.channel_layer.group_send(
            self.name+"_"+"all",
            {
            "type" : "websocket.broadcast",
            "what" : "close",
            "who" : self.who,
            "message" : "{} Disconnected".format(self.who)
            }
        )
        raise StopConsumer


    async def websocket_broadcast(self, event):
        print("Broadcasting...", event)
        what = event["what"]
        message = event["message"]
        if what == "open":    
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "open" : message,
                    "recv" : "open",
                    "who" : event["who"] 
                })
            })
        elif what == "close":
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "close":message,
                    "recv" : "close",
                    "who" : event["who"]
                })
            })
        elif what == "offer":
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "recv" : "offer",
                    "offer": message
                })
            })
                
        elif what == "answer":
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "recv" : "answer",
                    "answer" : message
                })
            })
        elif what == "iceCand":
            await self.send({
                "type" : "websocket.send",
                "text" : json.dumps({
                    "recv" : "iceCand",
                    "candidate": message
                })
            })