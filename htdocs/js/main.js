var dummyStatus = {
    num_badges: 123,
    num_gateways: 2
}

function updateHeader(status) {
    var template = $('#tpl-header').html();
    Mustache.parse(template);
    var rendered = Mustache.render(template, status);
    $('#fillme-header').html(rendered);
}

function updateGateways(status) {
    var template = $('#tpl-gwlist').html();
    Mustache.parse(template);
    var rends = []
    for(cid in status.gateways) {
        var gateway = status.gateways[cid];
        console.log(cid, gateway);
        var rendered = Mustache.render(template, gateway);
        rends.push(rendered);
    }
    console.log("RENDERED:", rends);
    $('#fillme-gwlist').html(rends.join("\n"));
}

function updateNotes(notes) {
    console.log("set notes to", notes);
    var template = $('#tpl-note').html();
    Mustache.parse(template);
    var rends = []
    for(var i=0; i<notes.length; i++) {
        var rendered = Mustache.render(template, notes[i]);
        rends.push(rendered);
    }
    console.log("rends", rends);
    $('#fillme-notes').html(rends.join("\n"));
}

function updateAll(status) {
    console.log("Updating status", status);
    updateHeader(status);
    updateGateways(status);
}

var ws;
var notes = [];

function addNote(time, msg) {
    notes.push({'time':time, 'msg':msg});
    // cap at 10
    if(notes.length == 11) notes = notes.slice(1);
    updateNotes(notes);
}

function onWsMessage(msgstr) {
    var msg = JSON.parse(msgstr);
    switch(msg.type) {
        case 'note':
            addNote(msg.time, msg.text);
            break;
        default:
            console.warn("Unhandled ws msg type", msg);
    }
}

function setupWebsocket() {
    ws = new WebSocket("ws://" + location.hostname+(location.port ? ':'+location.port: '') + "/ws");
    ws.onopen = function() {
        console.log("WS Connected");
       //ws.send("Hello, world");
    };
    ws.onmessage = function (evt) {
        console.log("wsmsg",evt);
       onWsMessage(evt.data);
    };
    ws.onclose = function () {
        console.warn("WS Connected");
    };
    ws.onerror = function () {
        console.warn("WS error");
    };
}

$(document).ready(function(){
    $.get("/status.json", function(status) {
        console.log("new status:", status);
        updateAll(status);
    });
    setupWebsocket();
});
