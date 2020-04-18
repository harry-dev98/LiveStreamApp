"use strict"
const configuration = {'iceServers':[{urls:['turn:conf.zedderp.com'],username:'zeddlabz',credential:'&io1vb%QM^lZnG%61'}]};
var offerConstraints = {offerToReceiveAudio:1,offerToReceiveVideo:1};
let Users = [];
let user;
let userCnt=0;
let localStream;
let VStream;
let remoteDesc; 
let mediaRecorder;
let recordedBlobs;
let isLive=false;
let isStreaming=false;
var docWebSocket;

var video = document.getElementById('video');
let dropArea = document.getElementById('drop-area');
// let button = document.getElementById("button");
let msgBox = document.getElementById("chatBox");
let peers = document.getElementById("peerstatus");
// let btn_stream = document.getElementById("btn_stream");
let btn_live = document.getElementById("btn_live");
let liveTag = document.getElementById("live");
let sendmsg = document.getElementById("submit");
let txt = document.getElementById("txt");
let close = document.getElementById("close");

window.onbeforeunload = (e)=>{
    if(webCamSocket){
        webCamSocket.close();
    };
    if(videoSocket){
        videoSocket.close();
    }
    if(docWebSocket){
        docWebSocket.close();
    }
    // if()
}
close.onclick=(e)=>{
    stopStreaming();
    liveTag.style.opacity=0;
}

let fileCount = 0;
let files;

sendmsg.onclick = (e)=>{
    let m = txt.value;
    if(m!=""){
        txt.value="";
        for(const [u, U] of Object.entries(Users)){
            U.datachann.send(JSON.stringify({
                "message" : true,
                "text" : m,
                "sender" : name
            }))
        }
        let M = document.createElement('p');
        M.innerText = name+" : "+m;
        msgBox.appendChild(M);
    }
}

btn_live.onclick = (e)=>{
    isLive=true;
    console.log("livenow");
    liveTag.style.opacity = 1;
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
    // if(isLive){
        stopStreaming();
        if(mediaRecorder)
            mediaRecorder.pause();
        // setTimeout(
        //     mediaRecorder.stop(),
        //     1000
        // );
        liveTag.style.opacity=0;
        isStreaming=false;
        btn_live.style.display = "block";
    }
    console.log("pauseddd")
    // btn_stream.style.display = "none";
}
video.onplay=(e)=>{
    console.log(isLive, isStreaming);
    if(!isStreaming && isLive){
    // if(isLive &&){
        startStreaming();
        if(mediaRecorder){
            mediaRecorder.resume();
        }
        else{
            startRecording();
        }
        isStreaming=true;
        liveTag.style.opacity=1;
        btn_live.style.display = "none";
    }
    else{
        // video.pause();
    }
    console.log("plahying videosss");
}

function addImg(file){
    let img = document.createElement('iframe');
    img.src = file;
    img.alt="Failed To Load Image";
    img.setAttribute('width', '100%');
    img.setAttribute('height', '100%');
    msgBox.appendChild(img);

}
function addpdf(file){
    var ifrm = document.createElement('iframe');
    ifrm.height = "100%";
    ifrm.width = "100%";
    ifrm.src = file;
    msgBox.appendChild(ifrm);
}

dropArea.onchange = (e)=>{
    let file = e.target.files[0];
    dropArea.value = "";
    docWebSocket = new WebSocket(
        'wss://' + window.location.host + '/ws/doc/'+sess
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
    async function send_then_preview(file){
        for (const [user, U] of Object.entries(Users)){
            console.log("sending to user..", user);
            let DataChann = U.datachann;
            let promise_toSend = new Promise(async (resolve, reject)=>{
                if(file){
                    console.log("sending metadata");
                    let bool =await send_metaData(DataChann, file);
                    console.log("sending metadata");
                    if(bool){
                        resolve(DataChann, file);
                    }
                    else{
                        send_then_preview(file);
                    }
                } 
                else reject("no file to send");
            })
            
            await promise_toSend
            .then(await send_chunks(DataChann, file))
            .then(await preview(file))
            .catch((err)=>{
                preview(file);
                console.log(err);
            });
        }
    }
    send_then_preview(file);
}

async function send_metaData(DataChann, file){
    return new Promise(async(resolve, reject)=>{
        try{
            console.log("metadata sending of "+file.name);
            let name = file.name;
            let size = file.size;
            let type = file.type;
            let d = {
                "metaData" : true,
                "file" : name,
                "size" : size,
                "type" : type
            }
            let send_d = JSON.stringify(d);
            await DataChann.send(send_d);
            
            console.log("metadata sent of "+file.name);
            resolve("DONE");
        }
        catch(e){
            reject(e);
        }
    })
    // await webCamSocket.send(send_d);
}
async function send_chunks(DataChann, file){
    console.log("sending chunks of "+file.name);
    let chunk = 16 * 1024  //* 1024;
    let left = file.size;
    let offset = 0;
    let slice;
    let fileReader = new FileReader();
    fileReader.onerror = (e)=>{
        console.log("error reading file.. ",e);
    };
    fileReader.onabort = (e)=>{
        console.log("aborted reading a file", e);
    };
    fileReader.onload = async (e)=>{
        // console.log("file chunk Loaded..", e);
        await DataChann.send(e.target.result);
        // await docWebSocket(e.target.result);
        // await webCamSocket.send(slice);
        if(left!=0){
            readChunks();
        }
    }
    async function readChunks(){
        chunk = (chunk > left) ? left : chunk;
        slice = file.slice(offset, offset+chunk);
        // console.log(slice);
        fileReader.readAsArrayBuffer(slice);
        left -= chunk;
        offset += chunk;
        console.log("sent ",(file.size-left),"/",file.size);
    }
    await readChunks(0);
    console.log("sent file.. "+ file.name);   
}

function preview(file){
    var objectURL = URL.createObjectURL(file);
    var Ext = file.name.substring(file.name.lastIndexOf('.') + 1).toLowerCase();
    console.log("extension of file is "+ Ext);
    if (Ext=="gif"||Ext=="png"||Ext=="bmp"||Ext=="jpeg"||Ext=="jpg"){
        addImg(objectURL);
    }
    else if(Ext == "pdf"){
        addpdf(objectURL);
    }
    console.log("added files...");
    return file;
}

function _util_extract_video(stream){
    let V = stream.getVideoTracks();
    VStream = new MediaStream();
    VStream.addTrack(V[0]);
    video.srcObject = VStream;
    // video.play();
}   

function getStream(){
    if(navigator.mediaDevices){
        console.log("need permissions to user media devices");
        navigator.mediaDevices.getUserMedia({
            audio: {
            echoCancellation: {exact: true}
            },
            video: {
            width: 640, height: 480
            }
        })
        .then(stream=>{
            console.log("media devices acquired..");
            localStream = stream;
            _util_extract_video(stream);
            return stream;
        })
        .then(()=>{
            if(isLive && isStreaming){
                console.log("started recording..")
                startRecording();
            }
        })
        .catch(err=>{
            console.log("error while accesing media", err);
        })
    }
}
getStream();
function stopStreaming(){
    for (const [user, U] of Object.entries(Users)){
        let senders = U.conn.getSenders();
        console.log("stopppingg streaminggg", senders);
        senders.forEach((sender)=>{
            console.log(sender);
            U.conn.removeTrack(sender);
        });
    };
}
function startStreaming(){
    for (const [user, U] of Object.entries(Users)){
        let Conn = U.conn;
        // getStream();
        console.log("Starting streamingg for "+user);
        
        localStream.getTracks().forEach(track => Conn.addTrack(track, localStream));
        offer(Conn, user);
    }
}
let totB = 0;
function startRecording() {
    recordedBlobs = [];
    let options = {
        mimeType : 'video/webm;codecs=vp9'
    };
    if(!MediaRecorder.isTypeSupported(options.mimeType)){
        console.log(options.mimeType, " is not supported!!");
        options = {
            mimeType : 'video/webm;codecs=vp8,opus'
        };
        if(!MediaRecorder.isTypeSupported(options.mimeType)){
            console.log(options.mimeType, " is not supported!!");
            options = {
                mimeType : 'video/webm'
            };
            if(!MediaRecorder.isTypeSupported(options.mimeType)){
                console.log(options.mimeType, " is not supported!!");
                options = {
                    mimeType : ''
                };
            }
        }    
    }
    try{
        mediaRecorder = new MediaRecorder(localStream, options);
        if( videoSocket.readyState == WebSocket.CLOSED){
            videoSocket = new WebSocket(
                'wss://' + window.location.host + '/ws/videos/'+sess
            );
        }
    }
    catch(err){
        console.log("Not recording.. ", err);
    }
    mediaRecorder.onstop = (event)=>{
        console.log("socket clossingg, recording stopped");
        videoSocket.close();
    }
    mediaRecorder.ondataavailable = (event)=>{
        if(event.data && event.data.size>0){
            // console.log("sending..", event.data);
            // recordedBlobs.push(event.data);
            videoSocket.send(event.data);
        }
    }
    mediaRecorder.start(1000);
}

function download(){
    // mediaRecorder.stop();
    const blob = new Blob(recordedBlobs, {type:'video/webm'});
    // recordedBlobs = [];
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = sess + '.webm';
    a.click();
    window.URL.revokeObjectURL(url);
}

let offer = async (Conn, user)=>{
    console.log("creating an offer for ", user);
    await Conn.createOffer(offerConstraints)
    .then(async (offer)=>{
        console.log("setting local Description..");
        await Conn.setLocalDescription(offer);
        return Conn.localDescription;
    })
    .then(async (desc)=>{
        console.log("sending offer... host is live == ", isLive);
        await webCamSocket.send(JSON.stringify({
            "offer" : desc,
            "for" : user,
            "isLive": isLive
        }))
    })
    .catch((err)=>{
        console.log("there was trouble sending offer...", err);
        setTimeout(offer, 1000);
    })

};
webCamSocket.onclose = (event)=>{
    console.log("socket is closeddd");
    setTimeout(()=>{
        let webCamSocket = new WebSocket(
            'wss://' + window.location.host + '/ws/rooms/'+sess+'/'+"peer_"+id
        );
        
        webCamSocket.onopen = function(e){
            console.log("Socket is connected");
            }
        }, 3000);
}
webCamSocket.onmessage = (event)=>{
    let data = JSON.parse(event.data);
    // console.log("websocket recieved a message..",data.recv);
    console.log(data.message);
    if(data.recv == "answer"){
        console.log("recieved a answer..");
        let ansDesc = data["answer"];
        user = data["by"]
        console.log(Users[user]);
        let Conn = Users[user]["conn"];
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
            await Conn.setRemoteDescription(ans);
        })
        .catch((err)=>{
            console.log("encountered error while setting remote Desc")
        }));
    }
    else if(data.recv == "iceCand"){
        user = data.by;
        try{
            console.log("adding candidates..");
            Users[user]["conn"].addIceCandidate(data["candidate"]);
        }
        catch(e){
            console.log("error occured while adding candidates.. ", e);
        }
    }
    else if(data.recv == "open"){
        console.log(data.open)
    }
    else if(data.recv == "close"){
        console.log(data.close);
    }
    else if(data.recv == "close_broadcast"){
        console.log("a peer left..");
        if(typeof Users[data.user] != "undefined"){
            Users[data.user]["conn"].close();
            Users[data.user]["datachann"].close();
            delete Users[data.user];
            peers.innerText = "Active "+(Object.keys(Users).length);
        }
        else{
            console.log("no such user");
        }

    }
    else if(data.recv == "open_broadcast"){
        console.log(data.open_broadcast); 
        user = data.user;
        if(typeof Users[user] == "undefined"){
        // console.log(peers.innerText, userCnt);
            Users[user] = {
                "userId" : data.userId,
                "conn" : new RTCPeerConnection(configuration)
            };
            Users[user]["datachann"] = Users[user]["conn"].createDataChannel(user+"_datachann");
            Users[user]["datachann"].binarayType = "arraybuffer"
            peers.innerText = "Active "+(Object.keys(Users).length);
        }
        console.log("created instance of a new user.. conn aswell as data channel")
        new Promise((resolve, reject)=>{
            try{
                resolve(data.user);
            }
            catch(err){
                reject(err);
            }
        })
        .then((u)=>{
            let U = Users[u];
            let Conn = U.conn;
            let Chann = U.datachann;
            Conn.onicecandidate = async (event)=>{
                console.log("Add the connections.. of ", user);
                const iceCand = event.candidate;
                if(iceCand){
                    await webCamSocket.send(JSON.stringify({
                        "who" : "host",
                        "for" : user,
                        "candidate" : iceCand
                    }));
                }
            };
            Conn.oniceconnectionstatechange = (event)=>{
                let state = Conn.iceConnectionState;
                console.log("state of connection is ", state);
                if(state == "closed" || state == "disconnected" || state == "failed"){
                    if(Conn){
                        offer(Conn, user);
                    }
                }
            };
            Conn.onerror = (event)=>{
                peers.innerText = "Active "+(Object.keys(Users).length);
                console.log(U.user+" Conn encountered an error "+event);
            };
            Conn.onclose = (event)=>{
                peers.innerText = "Active "+(Object.keys(Users).length);
                console.log("conn close");
                delete Users[U.user];
            }
            Chann.onopen = (event)=>{   
                console.log(U.user+" Channel's ready state is "+ Chann.readyState);
            };
            Chann.onclose = (event)=>{
                console.log(U.user, " Channel's ready state is ", Chann.readyState);
            };
            Chann.onerror = (event)=>{
                console.log("Error in DataChannel for "+ U.user+" "+event);
            };
            Chann.onnegotiationneeded = (e)=>{
                console.log("connection negotiated...");
            };
            Conn.ondatachannel = (event)=>{
                var recvChann = event.channel;
                recvChann.onmessage = (event)=>{
                    let m = JSON.parse(event.data);
                    let M = document.createElement('p');
                    M.innerText = m.sender+" : "+ m.text;
                    msgBox.appendChild(M);
                };
            };
            if(isLive==true && isStreaming==true){
                localStream.getTracks().forEach(track => Conn.addTrack(track, localStream));
                offer(Conn, user);
            }
        })
        .catch((e)=>{
            console.log("error", e);
        });
    }
}

setInterval(()=>{
    sessionStorage.clear();
}, 10000)