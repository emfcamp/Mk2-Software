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
    console.log("gatewas", status.gateways);
    for(cid in status.gateways) {
        var gateway = status.gateways[cid];
        console.log(cid, gateway);
        var rendered = Mustache.render(template, gateway);
        rends.push(rendered);
    }
    console.log("RENDERED:", rends);
    $('#fillme-gwlist').html(rends.join("\n"));
}

function updateAll(status) {
    console.log("Updating status", status);
    updateHeader(status);
    updateGateways(status);
}

$(document).ready(function(){
    $.get("/status.json", function(status) {
        console.log("new status:", status);
        updateAll(status);
    });
});
