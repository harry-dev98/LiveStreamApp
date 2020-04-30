"use strict"
const configuration = {sdpSemantics: 'unified-plan',iceServers: [{urls:['turn:conf.zedderp.com'],username:'zeddlabz',credential:'&io1vb%QM^lZnG%61'}]};

let pc;
var User;
var isPeer = true;
var remoteStream;
var isLive = false;
var localStream;
var VStream;
var host_status = 3;
// host_status === 1 => web Streaming
// host_status === 2 => host is online but not live
// host_status === 3 => host_status offline

var video = document.getElementById('video');
console.log(video);
var msgBox = document.getElementById('chat-box');
var liveTag = document.getElementById('live');
var sendmsg = document.getElementById("msg-send");
var txt = document.getElementById("msg-box");
var sessinfo = document.getElementById('sessinfo');
// var hd = document.getElementById('hd');
var pixels = '360p';

// hd.onclick=(e)=>{
//     if(pixels == '360p'){
//         pixels = '720p';
//         hd.innerHTML = "Low";
//     }
//     else if(pixels == "720p"){
//         pixels = '360p';
//         hd.innerHTML = "HD";
//     }
//     requestOffer();
// }
window.onload = e=>{
    getStream();
}
async function _util_extract_video(stream){
    let V = await stream.getVideoTracks();
    VStream = new MediaStream();
    VStream.addTrack(V[0]);
    video.srcObject = VStream;
    // video.play();
} 

function getStream(){
    if(navigator.mediaDevices){
        navigator.mediaDevices.getUserMedia({
            audio: {

                echoCancellation: {exact: true}
            },
            video: {
            width: 2560, height: 1440
            // width: 640, height: 360
            }
        })
        .then(async (stream)=>{
            console.log("media devices acquired..");
            await _util_extract_video(stream);
            localStream = stream;
        })
        .catch(err=>{
            console.log("error while accesing media", err);
        })
    }
}


function sendMsg(e){
    let m = txt.value;
    if(m!=""){
        txt.value="";
        messageSocket.send(JSON.stringify({
                "message" : "M!~!"+m,
                "sender":name
            }));
        let M = document.createElement('p');
        M.setAttribute("id", "mine");
        M.setAttribute("class", "chat");
        M.innerText = "Me:~\n"+m;
        msgBox.appendChild(M);
    }
}

function addDoc(objURL, fname)
{
    var p = document.createElement('a');
    var ifrm = document.createElement('iframe');
    ifrm.setAttribute('height', '100%');
    ifrm.setAttribute('width', '100%'); 
    ifrm.src = objURL;
    p.innerHTML = "---Tap to Download---"
    p.style.display = "block";
    p.style.textAlign = "center";
    p.href = ifrm.src;
    p.download = fname;
    // ifrm.onload=(e)=>{
    //     p.click();
    //     p.remove();
    //     URL.revokeObjectURL(ifrm.src);
    // }    
    msgBox.appendChild(ifrm);
    msgBox.appendChild(p); 
}

messageSocket.onmessage=(e)=>{
    let data = JSON.parse(e.data);
    console.log(data);
    const [type, msg] = data.message.split('!~!');
    if(type == "L"){
        let href = "http://"+window.location.host +"/media/"+ downDir + "documents/" + msg;
        console.log(href);
        addDoc(href, msg);
    }
    else if(type == "M" && data.sender != name){
        let M = document.createElement('p');
        M.setAttribute("id", "notmine");
        M.setAttribute("class", "chat");
        M.innerText = data.sender+" : "+msg;
        msgBox.appendChild(M);
    }
    else{
        console.log("unusual event!! Type : ", type);
    }
}

function reEstablishConnection(){
    signalSocket.close();
}

pc = new RTCPeerConnection(configuration);
pc.onicegatheringstatechange= (e)=>{
    console.log("icegatheringstate :: ", pc.iceGatheringState);
};

pc.oniceconnectionstatechange = (e)=>{
    console.log("iceconnectionstate :: ", pc.iceConnectionState);
    if(pc.iceConnectionState == "failed" || pc.iceConnectionState == "disconnected"){
        signalSocket.close();
        new Promise((resolve)=>{
            if(signalSocket.readyState == signalSocket.OPEN){
                resolve();
            }
            else{
                signalSocket.onopen=(e)=>{
                    console.log("established connection again");
                    resolve();
                }
            }
        }).then(()=>{
            return requestOffer();
        })
        .catch((err)=>{
            console.log("caught error", err);

        });
    }
}
    
pc.onsignalingstatechange = (e)=>{
    console.log("signalingstate :: ", pc.signalingState);
};

pc.ontrack = (e)=>{
    console.log("recieved a track ", e.track.kind);
    video.srcObject = e.streams[0];
};

function requestOffer(){
    console.log("sending request to get offer")
    signalSocket.send(JSON.stringify({
        "requestOffer":1,
        "pixels" : pixels
    }));
}

signalSocket.onmessage = (event)=>{
    let data = JSON.parse(event.data);
    console.log(data.message);
    console.log(data);
    if(data.offer){
        // receiving offer
        new Promise((resolve)=>{
            resolve(new RTCSessionDescription({sdp:data.sdp, type:data.type}));
        })
        .then((desc)=>{
            pc.setRemoteDescription(desc);
            new Promise((resolve)=>{
                if(pc.signalingState == "have-remote-offer"){
                    console.log("resolving due to remote desc");
                    resolve();
                }
                else{
                    function checkSignalingState(){
                        if(pc.signalingState == "have-remote-offer"){
                            pc.removeEventListener("signalingstatechange", checkSignalingState);
                            console.log("resolving due to remote desc");
                            resolve();
                        }
                    }
                    pc.addEventListener("signalingstatechange", checkSignalingState);
                }
            })
            .then(async()=>{
                let answer = await pc.createAnswer();
                // console.log(answer);
                pc.setLocalDescription(answer);
                new Promise((resolve)=>{
                    if(pc.signalingState == "stable"){
                        console.log("resolving due to stable");
                        resolve();
                    }
                    else{
                        function checkSignalingState(){
                            if(pc.signalingState == "stable"){
                                pc.removeEventListener("signalingstatechange", checkSignalingState);
                                console.log("resolving due to stable");
                                resolve();
                            }
                        }
                        pc.addEventListener("signalingstatechange", checkSignalingState);
                    }
                })
                .then(async()=>{
                    let answer = pc.localDescription;
                    // console.log("answer is ", answer.sdp);
                    // console.log("offer is ", pc.remoteDescription.sdp);
                    return await signalSocket.send(JSON.stringify({
                        "answer" : "answer",
                        "sdp" : answer.sdp,
                        "type" : answer.type
                    }))
                });
            });
        })
        .catch((err)=>{
            console.log(err);
            requestOffer();
        });
    }
    else if(data.ack){
        console.log("connection acknowledged");
        if(data.ack == 1){
            sessinfo.innerHTML = "Have Patience, Webinar Will Start Soon. Don't Reload!!";
        }
    }
    else if(data.bye){
        isLive = false;
        liveTag.style.opacity=0;
    }

    else if(data.live==1){
        if(host_status == 3){
            signalSocket.send({
                "ack_host" : 1,
                "user" : User
            })
        }
        isLive = true;
        host_status = 1;
        liveTag.style.opacity=1;
        sessinfo.style.display="none";
        requestOffer();
    }
    
    else if(data.live==0){
        host_status = 2;
        isLive = false;
        sessinfo.style.display="block";
        liveTag.style.opacity=0;
        console.log("transceivers",pc.getSenders);
        let senders = pc.getSenders();
        senders.forEach((sender)=>{
            pc.removeTrack(sender);
        });
    }

    else if(data.answer){
        //never occuring event
    }
    else if(data.open){
        //socket open
    }
    else if(data.close){
        //socket close 
    }
    else if(data.open_broadcast){
        //host logged in
        sessinfo.innerHTML = "Have Patience, Webinar Will Start Soon. Don't Reload!!";
    }
    else if(data.close_broadcast){
        //host logged out
        isLive = false;
        liveTag.style.opacity=0;
        sessinfo.innerHTML = "Please wait. Don't Reload!! Stay Connected";
        sessinfo.style.display = "block";
    }
    else{
        //any event if left
    }
}

