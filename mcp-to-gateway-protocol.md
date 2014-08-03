# MCP to GW protocol

* TCP, established from the GW to the MCP.
* Port 36000, no TLS (yet)
* The GW has to send initial information after the connection has been established
* Messages can go both ways after that
* Ever message is a json encoded line followed by a newline ("\n")
* The connection should not be termniated under normal circumstances

## Initial information (from GW to MCP)
```
{
    "type": "initial",
    "numberOfRadios": 2,
    "identifier": "A12", <optional, but has to be 3 ASCII long>
    "radios": [{
            "path": "/dev/ttyACM1",
            "firmware" : "xxxx"
        }, {...}
    ]
}
```

## Messages send from MCP to GW
Configure radio
{
    "type": "configure",
    "radioId": 0, <between 0 and numberOfRadios(exclusive)>
    "configuration": ["ATPK3A", "ATAC", "ATDN"]
}

Send packet
{
    "type": "send",
    "radioId": 0, <between 0 and numberOfRadios(exclusive)>
    "payload": "" <hex encoded message, 58bytes>
}

## Message send from GW to MCP
Received packet
{
    "type": "received",
    "radioId": 0,
    "payload": "", <hex encoded message, 58bytes>
    "rssi": -28
}