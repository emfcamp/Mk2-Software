Software
========

PC Software for using the TiLDA v2

## mcp
This is the bit that's managing all communication to and from the gateways. It listens for TCP connections on port 36000

## gateway
The gateway software runs on small clients that are equipped with 2 or more usb radios. On startup they'll establish connections to the ,mcp.


## Developing

With VirtualBox and Vagrant installed, run:

    $ vagrant up
    $ vagrant ssh
    $ cd /vagrant/  # this is the mounted dir from your host

etc.

## API

Anything like sending regular weather reports or whatever should be
written as a script, cronned, and deliver messages via the http api.

We'll want helper-handlers, like posting to /send-weather or something.

Send a message:

    curl -XPOST -d "hello" "http://localhost:8888/send?rid=1&connection=2"


