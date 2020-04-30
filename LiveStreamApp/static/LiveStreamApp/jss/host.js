"use strict"
const configuration = {sdpSemantics: 'unified-plan',iceServers: [{urls:['turn:conf.zedderp.com'],username:'zeddlabz',credential:'&io1vb%QM^lZnG%61'}]};

let pc;
let localStream;
let VStream;
let remoteDesc; 
let isLive=false;
let isStreaming=false;
let docWebSocket;
let Users = [];

var video = document.getElementById('video');
let dropArea = document.getElementById('drop-area');
let msgBox = document.getElementById("chat-box");
let peers = document.getElementById("peerstatus");
let btn_live = document.getElementById("btn_live");
let liveTag = document.getElementById("live");
let sendmsg = document.getElementById("msg-send");
let txt = document.getElementById("msg-box");
let close_btn = document.getElementById("close");
window.onload = e=>{
    getStream();
}

function createPC(){
    pc = new RTCPeerConnection(configuration);
    pc.onicegatheringstatechange= (e)=>{
        console.log("icegatheringstate :: ", pc.iceGatheringState);
    }
    
    pc.oniceconnectionstatechange = (e)=>{
        console.log("iceconnectionstate :: ", pc.iceConnectionState);
    }
    
    pc.onsignalingstatechange = (e)=>{
        console.log("signalingstate :: ", pc.signalingState);
    }
    
    pc.ontrack = (e)=>{
        console.log("recieved a track ", e.track.kind);
    }
}

createPC();

close_btn.onclick=(e)=>{
    stopStreaming();
    liveTag.style.opacity=0;
}

function notifyUser(user, status){
    let M = document.createElement('p');
    M.style.textAlign = "center";
    M.style.fontSize = '15px';
    M.innerHTML = user + " " + status;
    peers.innerText = "Active "+ Users.length;
    console.log("updating active, ", status, Users.length);
    msgBox.appendChild(M);
}

function sendMsg(e){
    console.log(e);
    let m = txt.value;
    if(m!=""){
        txt.value="";
        messageSocket.send(JSON.stringify({
            "message" : "M!~!"+m,
            "sender": name
        }));
        let M = document.createElement('p');
        M.setAttribute("id", "msg-right");
        M.innerText = "Me:~\n"+m;
        msgBox.appendChild(M);
        
    }
}


messageSocket.onmessage=(e)=>{
    let data = JSON.parse(e.data);
    const [type, msg] = data.message.split('!~!');
    if(type == "M" && data.sender != name){
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


btn_live.onclick = (e)=>{
    console.log("livenow");
    isLive = true;
    btn_live.style.display="none";
    if(video.paused){
        video.play();
    }
    else{
        video.pause();
        video.play();
    }
}


video.onpause = (e)=>{
    console.log(isLive, isStreaming);
    if(isStreaming && isLive){
        stopStreaming();
        liveTag.style.opacity=0;
        isStreaming=false;
        btn_live.style.display = "block";
    }
    console.log("pauseddd")
}
video.onplay=(e)=>{
    console.log(isLive, isStreaming);
    if(!isStreaming && isLive){
        startStreaming();
        isStreaming=true;
        // liveTag.style.opacity=1;
        btn_live.style.display = "none";
    }
    else{
        video.pause();
    }
    console.log("playing videosss");
    return new Promise((resolve)=>{
        if(pc.iceConnectionState == "connected" || pc.iceConnectionState == "completed"){
            resolve();
        }
        else{
            function checkState(){
                if(pc.iceConnectionState == "connected" || pc.iceConnectionState == "completed"){
                    pc.removeEventListener("iceconnectionstatechange", checkState);
                    resolve();
                }
            }
            pc.addEventListener("iceconnectionstatechange", checkState);
        }
    }).then(()=>{
        liveTag.style.opacity=1;
    })
}

function addDoc(objURL){
    var ifrm = document.createElement('iframe');
    ifrm.setAttribute('height', '100%');
    ifrm.setAttribute('width', '100%'); 
    ifrm.src = objURL; 
    msgBox.appendChild(ifrm);
}

dropArea.onchange = (e)=>{
    let file = e.target.files[0];
    messageSocket.send(JSON.stringify({
        "message" : "L!~!" + file.name,
        "sender" : name
    }));
    dropArea.value = "";
    docWebSocket = new WebSocket(
        'ws://' + window.location.host + '/ws/rooms/'+sess +"/doc"
    );
    docWebSocket.onopen=(e)=>{
        let fr = new FileReader();
        fr.onload = (e)=>{
            docWebSocket.send(JSON.stringify({
                "file" : file.name,
                "data" : e.target.result,
            }));
            docWebSocket.close();
        }
        fr.readAsDataURL(file);
        // fr.readAsBinaryString(file);
    }
    preview(file);
}

function preview(file){
    var objectURL = URL.createObjectURL(file);
    var Ext = file.name.substring(file.name.lastIndexOf('.') + 1).toLowerCase();
    console.log("extension of file is "+ Ext);
    // if (Ext=="gif"||Ext=="png"||Ext=="bmp"||Ext=="jpeg"||Ext=="jpg"){
    addDoc(objectURL);
    // }
    console.log("added files...");
}

function stopStreaming(){
    signalSocket.send(JSON.stringify({
        "isStreaming" : false,
        "live" : 0,
        "ack_to" : "all"
    }));
    
    let senders = pc.getSenders();
    // console.log("stopppingg streaminggg", senders);
    senders.forEach((sender)=>{
        pc.removeTrack(sender);
    });
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
            // width: 1280, height: 720
            width: 640, height: 360
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

function startStreaming(){
    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
    offer();
}

async function offer(){
    await pc.createOffer()
    .then(async (offer)=>{
        console.log("setting local Description..");
        return await pc.setLocalDescription(offer);
    })
    .then(async(offer)=>{    
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        })
    })
    .then(()=>{
        console.log("sending offer... host is live == ", isLive);
        var offer = pc.localDescription;
        // offer.sdp = sdpFilterCodec('audio', "opus/48000/2", offer.sdp);
        offer.sdp = sdpFilterCodec('audio', "PCMU/8000", offer.sdp);
        offer.sdp = sdpFilterCodec('video', "H264/90000", offer.sdp);
        return signalSocket.send(JSON.stringify({
            "offer" : "offer",
            "sdp" : offer.sdp,
            "type" : offer.type
        }))
    })
    .catch((err)=>{
        console.log("there was trouble sending offer...", err);
        setTimeout(offer, 1000);
    });
}

signalSocket.onmessage = (event)=>{
    let data = JSON.parse(event.data);
    console.log("received msgg...",data.message);
    // console.log(data);
    if(data.offer){
        // never occuring event
    }
    else if(data.renegotiate){
        // resend offer
        offer();
    }
    else if(data.answer){
        //recieve answer
        pc.setRemoteDescription(new RTCSessionDescription({sdp:data.sdp, type:data.type}))
        .then(()=>{
            signalSocket.send(JSON.stringify({
                "isStreaming" : isStreaming,
                "live" : 1,
                'ack_to' : "all"
            }));
        });
        console.log("connected");
    }
    else if(data.open_broadcast){
        //peer connected
        Users.push(data.user);
        notifyUser(data.user, "connected");
        signalSocket.send(JSON.stringify({
            "isStreaming" : true,
            "live" : 1,
            "ack_to" : data.user
        }));

    }
    else if(data.ack_host){
        console.log("ack_host");
        Users.push(data.user);
        notifyUser(data.user, "connected");
    }
    else if(data.close_broadcast){
        //peer disconnected
        Users.splice(Users.indexOf(data.user), 1);
        notifyUser(data.user, "disconnected");
    }
    else if(data.open){
        console.log("sockets connected");
    }
    else if(data.close){
        //dont care
    }
    else if(data.ack){
        console.log("everything workin good");
    }
    else{
        //ig no case left
    }
}



function sdpFilterCodec(kind, codec, realSdp) {
    var allowed = []
    var rtxRegex = new RegExp('a=fmtp:(\\d+) apt=(\\d+)\r$');
    var codecRegex = new RegExp('a=rtpmap:([0-9]+) ' + escapeRegExp(codec))
    var videoRegex = new RegExp('(m=' + kind + ' .*?)( ([0-9]+))*\\s*$')
    
    var lines = realSdp.split('\n');

    var isKind = false;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].startsWith('m=' + kind + ' ')) {
            isKind = true;
        } else if (lines[i].startsWith('m=')) {
            isKind = false;
        }

        if (isKind) {
            var match = lines[i].match(codecRegex);
            if (match) {
                allowed.push(parseInt(match[1]));
            }

            match = lines[i].match(rtxRegex);
            if (match && allowed.includes(parseInt(match[2]))) {
                allowed.push(parseInt(match[1]));
            }
        }
    }

    var skipRegex = 'a=(fmtp|rtcp-fb|rtpmap):([0-9]+)';
    var sdp = '';

    isKind = false;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].startsWith('m=' + kind + ' ')) {
            isKind = true;
        } else if (lines[i].startsWith('m=')) {
            isKind = false;
        }

        if (isKind) {
            var skipMatch = lines[i].match(skipRegex);
            if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
                continue;
            } else if (lines[i].match(videoRegex)) {
                sdp += lines[i].replace(videoRegex, '$1 ' + allowed.join(' ')) + '\n';
            } else {
                sdp += lines[i] + '\n';
            }
        } else {
            sdp += lines[i] + '\n';
        }
    }

    return sdp;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}