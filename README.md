# EMFCamp 2014 Badge Network Controller

The *MCP* program is the hub, run it on a server. The *gateway* code
runs on each raspberry pi, which all connect back to the MCP.

The gateways have the radios.

## Developing

With VirtualBox and Vagrant installed, run:

    $ vagrant up
    $ vagrant ssh
    $ cd /vagrant/  # this is the mounted dir from your host

## Running

    $ bin/mcp.py
    $ bin/gateway.py localhost abc

## API

Anything like sending regular weather reports or whatever should be
written as a script, cronned, and deliver messages via the http api.

We'll want helper-handlers, like posting to /send-weather or something.

Send a message:

    curl -XPOST -d "hello" "http://localhost:8888/send?rid=1&connection=2"

Query status of gateways:

    curl "http://localhost:8888/status.json"




