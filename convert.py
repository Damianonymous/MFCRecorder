#!/usr/bin/env python3
import asyncio
import sys
import os
from mfcauto import Client
import classes.config

conf = classes.config.Config(os.path.join(sys.path[0], 'config.conf'))
async def run(loop):
    client = Client(loop)
    await client.connect(False)
    with open(os.path.join(sys.path[0], sys.argv[1])) as source:
        for id in (int(line) for line in source.readlines()):
            if id not in conf.filter.wanted.dict.keys():
                msg = await client.query_user(id)
                if msg != None:
                    conf.filter.wanted.add(uid=id, custom_name=msg['nm'])
                    print("{} with uid {} added to list".format(msg['nm'], msg['uid']))

loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
