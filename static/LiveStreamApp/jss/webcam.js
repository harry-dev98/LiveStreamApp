    
var sdpConstraints ={
        offerToReceiveAudio:1,
        offerToReceiveVideo:1
    }

var isHost = false;
var isOffer = false;
var isAnswer = false;
var isDone = false;

var localStream;
var video = document.getElementById('video');


if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    .then(function(stream) {
        localStream = stream;
        video.srcObject = stream;
        video.play();
        // webCamSocket.send(stream);
    })
    .catch(function(err){
        console.log("errorrr", err)
    })
}


function handleConnectionChange(event){
    console.log("handling conn change..");
    console.log(event);
}
const configuration = {
    'iceServers': [{
        "urls": "stun:stun.l.google.com:19302"
    }]
};
let localPeerConn = new RTCPeerConnection(configuration);
localPeerConn.onicecandidate = async (event)=>{
    console.log("handling Connection..");
    const peerConn = event.target;
    const iceCandidate = event.candidate;
    console.log(peerConn);
    console.log(iceCandidate);
    if(iceCandidate){
        webCamSocket.send(JSON.stringify({
            "ice":1,
            "isHost":isHost,
            "candidate" : iceCandidate
        }));
    }
};
localPeerConn.addEventListener('iceconnectionstatechange', handleConnectionChange);
console.log("RTCPeerConnection object was created"); 
console.log(localPeerConn); 

async function sendOffer(){
    console.log("didnot recieved offer from server.. Creating a new offer")
    isOffer = true;
    isHost = true;
    await localPeerConn.createOffer(sdpConstraints)
    .then(function (offer){
        return localPeerConn.setLocalDescription(offer);
    })
    .then(function(){
        console.log("now ready to send offer");
        send_data = JSON.stringify({
            "offer": JSON.stringify(localPeerConn.localDescription)
        });
        console.log(send_data);
        webCamSocket.send(send_data);
    })
    .catch(function(err){
        console.log("error"+err);
    });
};

async function sendAnswer(){
    isAnswer = true;
    localPeerConn.createAnswer()
    .then(function (answer){
        return localPeerConn.setLocalDescription(answer);
    })
    .then(function(){
        console.log("sending.. answer");
        send_data = JSON.stringify({
            "answer": JSON.stringify(localPeerConn.localDescription)
        });
        webCamSocket.send(send_data);
    })
    .catch(function(err){
        console.log("error"+err);
    });
};

var wait = ms => new Promise((r, j)=>setTimeout(r, ms));

async function offerCreate(){
    if(webCamSocket.readyState == 1){
        await webCamSocket.send(
            JSON.stringify({
                "checkOffer":0
                }
            )
        );
        await wait(100);
        console.log("isOffer : "+isOffer);
        if(isOffer == false){
            await sendOffer();
        }
        else{
            console.log("offer has been created by someone..");
        }
    }
    else{
        console.log("waiting for websocket.. "+ webCamSocket.readyState)
        setTimeout(offerCreate, 1000);
    }
}
async function getAnswer(){
    if(isAnswer){
        isDone = true;
        return;
    }
    else{
        if(webCamSocket.readyState != 1){
            console.log("waiting for socket to connect..")
            setTimeout(getAnswer, 3000)
        }
        webCamSocket.send(
            JSON.stringify({
                    "checkAnswer":0
                }
            )
        );
        if(!isAnswer){
            console.log("waiting for answer..")
            setTimeout(getAnswer, 5000)
        }
    }
    isDone = true;
    return;
}

function getCand(){
    // await wait(1000);
    while(!isDone){
        console.log("waiting for candidates");
        // await wait(1000);
        // setTimeout(getCand, 1000);
    }
    webCamSocket.send(JSON.stringify({
        "isHost":isHost,
        "reqCand":1
    }))
}

function connect(callback){
    offerCreate();
    getAnswer();
    wait(10000);
    callback();
}

// connect(getCand);

webCamSocket.onmessage = async e => {
    var data = JSON.parse(e.data);
    console.log("recievedddd...\n",data);
    if(data.recv == "checkOffer"){
        console.log("offer available, hence setting isOffer true");
        isOffer = true;
        console.log("isOffer :" + isOffer);
        console.log(data["message"]);
        offer = JSON.parse(data["offer"]);
        console.log("creating remote desc of offer");
        const remoteDesc = new RTCSessionDescription(offer);
        await localPeerConn.setRemoteDescription(remoteDesc);
        await sendAnswer();
    }
    else if(data.recv == "true"){
        console.log(data["message"]);

    }
    else if(data.recv == "checkAnswer"){
        isAnswer = true;
        console.log(data["message"]);
        console.log("answer has been recieved.. ");
        ans = JSON.parse(data["answer"])
        const remoteDesc = new RTCSessionDescription(ans);
        await localPeerConn.setRemoteDescription(remoteDesc);
    }
    else if(data.recv == 'iceCand'){
        try{
            console.log("adddingg the candidate")
            await localPeerConn.addIceCandidate(data["candidate"]);
        }
        catch(e){
            console.error("Error adddingg the candidate", e);
        }
    }
}
    