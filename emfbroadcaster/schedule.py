#!/usr/bin/env python
import logging
import json
import requests
import sys
import tinypacks
import psycopg2


dbstr = "host='localhost' dbname='schedule' user='tilda' password='tilda'"
conn = psycopg2.connect(dbstr)
conn.set_session(autocommit=True)
cursor = conn.cursor()


def show_usage_message():
    print "Usage: ./schedule.py <fri|sat|sun>"
    sys.exit(1)


dayname = sys.argv[1]

if dayname == "fri":
    rid = 40963
    day = 29
elif dayname == "sat":
    rid = 40964
    day = 30
elif dayname == "sun":
    rid = 40965
    day = 31
else:
    show_usage_message()

config = json.load(open('../etc/config.json'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('schedule')


def get_schedule_for_day_and_location(day, locid):
    sql = "select id, title, type_id, abstract, speaker_names, extract('epoch' from start_time), extract('epoch' from end_time), location_id, location_name, date_part('day', start_time) as day from event where date_part('day', start_time) = %s and location_id = %s"
    cursor.execute(sql, (day, locid))
    rows = cursor.fetchall()
    ret = []
    for row in rows:
        ret.append({"id": row[0],
                    "title": row[1],
                    "type": row[2],
                    "abstract": row[3],
                    "speaker_names": row[4],
                    "start_time": int(row[5]),
                    "end_time": int(row[6]),
                    "location_id": row[7],
                    })
    return ret


def type_name_to_id(t):
    types = {
        "lecture": 1,
        "installation": 2,
        "workshop": 3,
        "other": 4
    }
    if t in types:
        return types[t]
    else:
        return 4


def pack_location_day_data(loc, s):
    packed = tinypacks.pack(len(s))
    for event in s:
        start_timestamp = event['start_time']
        end_timestamp = event['end_time']
        type_id = type_name_to_id(event['type'])
        speaker = ""
        if 'speaker' in event:
            speaker = event['speaker']['full_public_name']
        packed += tinypacks.pack(event['location_id'])
        packed += tinypacks.pack(type_id)
        packed += tinypacks.pack(start_timestamp)
        packed += tinypacks.pack(end_timestamp)
        packed += tinypacks.pack(speaker)
        packed += tinypacks.pack(event['title'])
    return packed


cursor.execute("select distinct location_id from event where location_id is not null order by location_id")
locids = cursor.fetchall()

for locidtup in locids:
    loc = locidtup[0]
    s = get_schedule_for_day_and_location(day, loc)
    print s
    p = pack_location_day_data(loc, s)
    params = dict(rid=rid)
    logger.info("Uploading location %d...", loc)
    response = requests.post(url=config['mcpBroadcastEndpoint'], params=params, data=p)
    if (response.status_code == 200):
        logger.info("OK")
    else:
        logger.warn("ERROR!!!!! %s", response)
