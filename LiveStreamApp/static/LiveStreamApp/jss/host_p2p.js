var offerConstraints = {
    offerToReceiveAudio : 1,
    offerToReceiveVideo : 1
};

var isPeer = false;
var localStream;
var remoteStream;
var remoteDesc;

var video = document.getElementById('video');

const configuration = {
    'iceServers' : [{
        "urls" : "stun:stun.l.google.com:19302"
    }]
};

let localPeerConn = new RTCPeerConnection(configuration);
console.log("RTCPeerConn established...")

localPeerConn.onicecandidate = async (event)=>{
    console.log("handling the connections..");
    const iceCand = event.candidate;
    if(iceCand){
        await webCamSocket.send(JSON.stringify({
            "who" : "host",
            "candidate" : iceCand
        }));
    }
}
localPeerConn.oniceconnectionstatechange = (event)=>{
    console.log("handling the connection change...");
    console.log(event);
}

if(navigator.mediaDevices){
    navigator.mediaDevices.getUserMedia({
        video : true,
        audio : true
    })
    .then(stream=>{
        localStream = stream;
        video.srcObject = stream;
        video.play();
        return stream;
    })
    .then((stream)=>{
        // localPeerConn.addStream(stream);
        stream.getTracks().forEach(track => localPeerConn.addTrack(track, stream));
    })
    .catch(err=>{
        console.log("error while accesing media", err);
    })
}

let offer = async ()=>{
    console.log("creating an offer..");
    await localPeerConn.createOffer(offerConstraints)
    .then(async (offer)=>{
        console.log("setting local Description..");
        await localPeerConn.setLocalDescription(offer);
        return localPeerConn.localDescription;
    })
    .then(async (desc)=>{
        console.log("sending offer...");
        await webCamSocket.send(JSON.stringify({
            "offer" : desc
        }))
    })
    .catch((err)=>{
        console.log("there was trouble sending offer...", err);
        setTimeout(offer, 1000);
    })
};

function createOffer(){
    if(isPeer == false){
        return setTimeout(createOffer, 5000);
    }
    else{
        offer();
    }
}

createOffer();

webCamSocket.onmessage = (event)=>{
    data = JSON.parse(event.data);
    console.log("websocket recieved a message..", event);
    if(data.recv == "answer"){
        console.log("recieved a answer..");
        ansDesc = data["answer"];
        (new Promise(async (resolve, reject)=>{
            console.log("getting a session object from answer");
            try{
                resolve(new RTCSessionDescription(ansDesc));
            }
            catch(err){
                reject(err);
            } 
        })
        .then(async (ans)=>{
            console.log("setting remote Desc..");
            await localPeerConn.setRemoteDescription(ans);
        })
        .catch((err)=>{
            console.log("encountered error while setting remote Desc")
        }));
    }
    else if(data.recv == "iceCand"){
        try{
            console.log("adding candidates..");
            localPeerConn.addIceCandidate(data["candidate"]);
        }
        catch(e){
            console.log("error occured while adding candidates.. ", e);
        }
    }
    else if(data.recv == "open"){
        console.log(data.open)
        if(data.who == "peer"){
            isPeer = true;
        }
    }
}


