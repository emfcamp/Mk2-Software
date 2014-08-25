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

Query status of gateways:

    curl "http://localhost:8888/status.json"


## TODO schema

    CREATE TABLE gateway (
        id SERIAL PRIMARY KEY,
        hwid text NOT NULL
    );
    CREATE UNIQUE INDEX gateway_hwid ON gateway USING btree (hwid);

    CREATE TABLE badge (
        id SERIAL PRIMARY KEY,
        hwid text NOT NULL,
        date timestamp(0) without time zone,
        gwid integer NOT NULL REFERENCES gateway(id) ON DELETE RESTRICT
    );
    CREATE UNIQUE INDEX hwid_uniq ON badge USING btree (hwid);






