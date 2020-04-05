var offerConstraints = {
    offerToReceiveVideo : 1,
    offerToReceiveAudio : 1
};

var userId;
var User;
var isPeer = true;
var remoteStream;

var video = document.getElementById('video');

const configuration = {
    'iceServers' : [{
        "urls" : "stun:stun.l.google.com:19302"
    }]
};

let localPeerConn = new RTCPeerConnection(configuration);
console.log("RTCPeerConn established..");
localPeerConn.onicecandidate = (event)=>{
    console.log("handling the connections");
    const iceCand = event.candidate;
    if(iceCand){
        webCamSocket.send(JSON.stringify({
            "who" : "peer",
            "candidate" : iceCand
        }));
    }
}

localPeerConn.oniceconnectionstatechange = (event)=>{
    console.log("handling the connection change...");
    console.log(event);
}

localPeerConn.ontrack = (event)=>{
    console.log("recieved mediaa.. from host");
    video.srcObject = event.streams[0];
    video.play();
};

webCamSocket.onmessage = async (event)=>{
    data = JSON.parse(event.data);
    console.log("websocket recieved a message..", event);
    if(data.recv == "offer"){
        console.log("recieved a offer..");
        offerDesc = data["offer"];
        new Promise(async (resolve, reject)=>{
            console.log("getting a session object of offer");
            try{
                resolve(new RTCSessionDescription(offerDesc));
            }
            catch(err){
                reject(err);
            }
        }).then(async (offer)=>{
            console.log("setting remote Desc")
            await localPeerConn.setRemoteDescription(offer);
        })
        .catch((err)=>{
            console.log("got an error setting remote Desc..", err);
        })
        .finally(async ()=>{
            console.log("remote Desc has been set..")
            console.log("creating an answer to the offer");
            await localPeerConn.createAnswer()
            .then(async (answer)=>{
                console.log("localDesc has been set");
                await localPeerConn.setLocalDescription(answer);
                return localPeerConn.localDescription;
            })
            .then(async (desc)=>{
                console.log("sending answer..")
                await webCamSocket.send(JSON.stringify({
                    "answer": desc
                }));
            })
            // .then(()=>{
            //     stream.getTracks().forEach(track => pc.addTrack(track, stream));
            // })
        })
    }
    else if(data.recv == "iceCand"){
        try{
            console.log("adding candidates..");
            localPeerConn.addIceCandidate(data["candidate"]);
        }
        catch(err){
            console.log("error occured while adding candidates.. ", err);
        }
    }
    else if(data.recv == "open"){
        userId = data.user[0];
        User = data.user[1];
        console.log(User, "User is instantiated as ", userId);
    }

}