from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from django.shortcuts import redirect
from channels.db import database_sync_to_async
from django.shortcuts import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from .models import Session, Peer
from .mediaStream import VideoReqTrack, Streams

from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaRecorder, MediaPlayer


import logging
import datetime as dt
import os
import json
import pickle
import base64
# import ffmpeg

class docConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.sess = self.scope['url_route']['kwargs']['name']
        self.DOC_DIR = os.path.join(settings.MEDIA_ROOT, "{}/{}/documents".format(self.sess, str(dt.date.today())))
        print("printing ", event)
        if not os.path.isdir("media/{}".format(self.sess)):
            os.mkdir("media/{}".format(self.sess))
        
        await self.send({
            "type" : "websocket.accept",
        })
    async def websocket_receive(self, event):
        data = json.loads(event['text'])
        self.temp = open(os.path.join(self.DOC_DIR, data["file"]) , "wb")
        _, encoded = data["data"].split(",", 1)
        binary = base64.b64decode(encoded)
        self.temp.write(binary)
        # print(data["data"])
        self.temp.close()

    async def websocket_disconnect(self, event):
        await self.send({
            "type" : "websocket.close",
        })
        raise StopConsumer()

        
class consumer(AsyncConsumer):
    pc = None
    sess = ""
    User = ""
    groupName = ""
    sessId = None
    who = ""
    peer = None
    VID_DIR = ""

    async def exception_handler(self, error):
        print("exception_handler is handling :: ",error)
        await self.pc.close()
        await self.recorder.stop()
        if self.sessId and self.who=="host":
            self.sessId.isActive = False
            await database_sync_to_async(self.sessId.save)()
        self.peer.logout = dt.datetime.now()
        await database_sync_to_async(self.peer.save)()
        print("saving logout")
        await selfmp4.send({
            "type" : "websocket.disconnect"
        })
        raise StopConsumer()
    

    async def websocket_connect(self, event):
        try:
            await self.send({
                    "type" : "websocket.accept",
                })
            
            self.sess = self.scope['url_route']['kwargs']['name']
            _ = self.scope['url_route']['kwargs']['identity']
            self.VID_DIR = os.path.join(settings.MEDIA_ROOT, "{}/{}/videos".format(self.sess, str(dt.date.today())))
            who_id = _.split("_")
            self.who = who_id[0]
            self.peer = await database_sync_to_async(Peer.objects.get)(id=who_id[1])
            self.User = self.peer.name
            self.groupName = self.sess+"_"+self.who
            self.sessId = await database_sync_to_async(Session.objects.get)(pk=self.sess)
            await self.channel_layer.group_add(
                self.groupName,
                self.channel_name
            )
            await self.channel_layer.group_add(
                self.sess+"_"+"all",
                self.channel_name
            )
            
            if self.who == "host":
                self.sessId.isActive = True
                await database_sync_to_async(self.sessId.save)()

        except Exception as error:
            print("exception occured,,..", error)
            self.exception_handler(error)

    async def websocket_receive(self, event):
        try:
            data = json.loads(event["text"])

            if "ack_host" in data:
                await self.channel_layer.group_send(
                    self.sess+"_host",
                    {
                        "type" : "websocket.broadcast",
                        "what" : "ack_host",
                        "user" : data["user"]
                    }
                )

            if "live" in data:
                print("live status")

                return await self.channel_layer.group_send(
                    self.sess+"_peer",
                    {
                        "type" : "websocket.broadcast",
                        "isStreaming" : data["isStreaming"],
                        "ack_to" : data["ack_to"],
                        "live" : data["live"],
                        "what" : "live"
                    }
                )
            if "hi" in data:
                print("websocket incoming hi")
                self.pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[RTCIceServer("turn:conf.zedderp.com", "zeddlabz", "&io1vb%QM^lZnG%61")]))
                fname = "webinar_{}.mp4".format(dt.datetime.now().strftime('%H_%M'))
                fdir = os.path.join(self.VID_DIR,fname)
                self.recorder = MediaRecorder(fdir)
                # self.bh = MediaBlackhole()
                @self.pc.on("track")
                def on_track(track):
                    self.pc.addTrack(track)   
                    self.recorder.addTrack(track)              
                    if track.kind == "audio":
                        print("adding audio")
                        self.audio = track
                        
                    elif track.kind == "video":
                        print("adding video")
                        self.video = track
                          
                    @track.on("ended")
                    async def on_ended():
                        print("stoping recorder")
                        await self.recorder.stop()
                        # await self.bh.stop()
                # @self.pc.on("datachannel")
                # def on_datachannel(channel):
                #     print("datachannel recieved")
                #     @channel.on("message")
                #     def on_message(message):
                #         print("msg via datachnnel")
                #         if isinstance(message, str) and message.startswith("ping"):
                #             channel.send("pong" + message[4:])

                @self.pc.on("iceconnectionstatechange")
                async def on_iceconnectionstatechange():
                    print("iceConnState :: ", self.pc.iceConnectionState)
                    if self.pc.iceConnectionState == "failed":
                        print("closing pc")
                        await self.pc.close()

                if self.who == "host":
                    await self.channel_layer.group_send(
                        self.sess+"_peer",
                        {
                            'type' : 'websocket.broadcast',
                            'what' : 'open',
                            'message': "we got a Host {}..".format(self.User),
                            'user' : self.User
                        }
                    )
                    await self.send({
                        "type" : "websocket.send",
                        "text" : json.dumps({
                            "ack" : 1,
                            "message" : "GoodToGo"
                        })
                    })
                elif self.who == "peer":
                    if self.sessId.isActive:
                        await self.channel_layer.group_send(
                            self.sess+"_host",
                            {
                                'type' : 'websocket.broadcast',
                                'what' : 'open',
                                'message': "we got a new user {}..".format(self.User),
                                'user' : self.User
                            }
                        )
                        await self.send({
                            "type" : "websocket.send",
                            "text" : json.dumps({
                                "message" : "Session Active",
                                "ack" : 1
                            })
                        })
                    else:
                        await self.send({
                            "type" : "websocket.send",
                            "text" : json.dumps({
                                "message": "Session is Not Live/Expired",
                                "ack" : 0
                            })
                        })

                else:
                    pass

            if "offer" in data:
                print("recieved offer")
                # if data["isLive"] == False:
                print(data)
                sdp = data["sdp"]
                typ = data["type"]
                self.offer = RTCSessionDescription(sdp=sdp, type=typ)    
                await self.pc.setRemoteDescription(self.offer)
                print("sending answer")
                self.answer = await self.pc.createAnswer()
                await self.pc.setLocalDescription(self.answer)
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "message" : "incoming answer",
                        "answer": "answer",
                        "sdp" : self.answer.sdp,
                        "type" : self.answer.type
                    })
                })
                # await self.bh.start()
                await self.recorder.start()
                Streams.get_field(self.sess)
                Streams.add_track(self.sess, "audio", self.audio)
                Streams.add_track(self.sess, "video", self.video)
                return
            elif "answer" in  data:
                print("got asnwer")
                sdp = data["sdp"]
                typ = data["type"]
                answer = RTCSessionDescription(sdp=sdp, type=typ)
                await self.pc.setRemoteDescription(answer)
                print("dpone with answer")
                return await self.send({
                    "type":"websocket.send",
                    "text" : json.dumps({
                        "message" : "All exchange of answer/offer done.."
                    })
                })

            elif "requestOffer" in data:
                print('request for offer received')
                try:
                    pix = data["pixels"]
                    vidTrack = Streams.get_track(self.sess, "video", pix)
                    audTrack = Streams.get_track(self.sess, "audio")
                    self.pc.addTrack(vidTrack)
                    self.pc.addTrack(audTrack)
                    print("getting offer")
                    offer = await self.pc.createOffer()
                    await self.pc.setLocalDescription(offer)
                    print(self.pc.getSenders())
                    print("sending offer to peer")
                    return await self.send({
                        "type" : "websocket.send",
                        "text" : json.dumps({
                            "message" : "incoming offer",
                            "offer" : "offer",
                            "sdp" : self.pc.localDescription.sdp,
                            "type" : self.pc.localDescription.type
                        })
                    })
                except KeyError as err:
                    print("keyerrorr", err, Streams._streams.keys())
                    return await self.send({
                        "type" : "websocket.send",
                        "text" : json.dumps({
                            "ack" : 1
                        })
                    })
            elif "candidate" in data:
                if data["who"] == "peer":
                    await self.channel_layer.group_send(
                        self.sess+"_host",
                        {
                            "type":"websocket.broadcast",
                            "what":"iceCand",
                            "message": data["candidate"],
                            "by" : data["by"]
                        }
                    )
                else:
                    await self.channel_layer.group_send(
                        self.sess+"_peer",
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


    async def websocket_disconnect(self, event):
        await self.pc.close()
        self.peer.logout = dt.datetime.now()
        await database_sync_to_async(self.peer.save)()
        print("saving logout")
        if self.who=="host":
            # del Streams._streams[self.sess]
            print("Setting session False")
            # await self.recorder.stop()
            self.sessId.isActive = False
            await database_sync_to_async(self.sessId.save)()
            await self.channel_layer.group_send(
                self.sess+"_peer",
                {
                "type" : "websocket.broadcast",
                "what" : "close",
                "user" : self.User,
                "message" : "{}, host Disconnected".format(self.User)
                }
            )
        else:
            await self.channel_layer.group_send(
                self.sess+"_host",
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
        await self.channel_layer.group_discard(
            self.groupName,
            self.channel_name
        )
        await self.channel_layer.group_add(
        self.sess+"_"+"all",
        self.channel_name
        )
        raise StopConsumer("{} Disconnected".format(self.who))


    async def websocket_broadcast(self, event):
        # print(event)
        try:
            what = event["what"]
            print("Broadcasting... ", what)

            if what == "ack_host":
                await self.send({
                    "type" : "websocket.send",
                    "ack_host" : 1,
                    "message" : "there is a user befor host",
                    "user" : event["user"]
                })

            if what == "live":
                print(event)
                if event["ack_to"] == "all":
                    await self.send({
                        "type" : "websocket.send",
                        'text' : json.dumps({
                            "isStreaming" : event["isStreaming"],
                            "message" : "live event",
                            "live" : event["live"]
                        })
                    })


                elif event["ack_to"] == self.User:
                    await self.send({
                        "type" : "websocket.send",
                        'text' : json.dumps({
                            "isStreaming" : event["isStreaming"],
                            "message" : "live event",
                            "live" : event["live"]
                        })
                    })


                else:
                    pass
                
            if what == "open":    
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "open_broadcast" : 1,
                        "user" : event["user"],
                        "message": event['message']
                    })
                })
            elif what == "close":
                await self.send({
                    "type" : "websocket.send",
                    "text" : json.dumps({
                        "close_broadcast": 1,
                        "user" : event["user"],
                        "message":event['message']
                    })
                })

        except Exception as error:
            self.exception_handler(error)


class msgConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.sess = self.scope['url_route']['kwargs']['name']
        _ = self.scope['url_route']['kwargs']['identity']
        who_id = _.split("_")
        self.who = who_id[0]
        self.peer = await database_sync_to_async(Peer.objects.get)(id=who_id[1])
        self.User = self.peer.name
        self.groupName = self.sess+"_chatroom"
        self.sessId = await database_sync_to_async(Session.objects.get)(pk=self.sess)
        await self.channel_layer.group_add(
            self.groupName,
            self.channel_name
        )
        return await self.send({
            "type" : "websocket.accept"
        })

    async def websocket_disconnect(self, event):
        await self.send({
            "type" : "websocket.close"
        })
        raise StopConsumer()
    
    async def websocket_receive(self, event):
        data = json.loads(event["text"])
        if "message" in data:
            await self.channel_layer.group_send(
                self.groupName,
                {
                    "type" : "websocket.broadcast",
                    "message" : data["message"],
                    "sender" : data["sender"]
                }
            )

    async def websocket_broadcast(self, event):
        await self.send({
            "type" : "websocket.send",
            "text" : json.dumps({
                "sender" : event["sender"],
                "message" : event["message"]
            })
        })