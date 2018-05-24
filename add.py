#!/usr/bin/env python3
import asyncio
import sys
import os
import argparse
from mfcauto import Client
import classes.config

parser = argparse.ArgumentParser(description="Add models to the MFC list to enable or disable their recordings. If a model already exists, her values will be updated to any new values passed in the arguments",\
                                 usage=list(os.path.split(sys.argv[0]))[1] + ' [model display name or uid] [options]')
parser.add_argument("model",nargs="*"[0], help='REQUIRED: models name or uid.')
parser.add_argument('-n', '--custom_name', dest='custom_name', default=False, help='set a custom name for the model, otherwise the models current display name will be used.')
parser.add_argument('-c', '--comment', dest='comment', default=False, help='specify a comment or not for the user.')
parser.add_argument('-m', '--min_viewers', dest='min_viewers', type=int, default=False, help='set the minimum number of viewers this model must have before recording starts')
parser.add_argument('-s', '--stop_viewers', dest='stop_viewers', type=int, default=False, help='set the number of viewers in which the recording will stop (should be less than minviewers')
parser.add_argument('-l', '--list_mode', dest='list_mode', default=False, help='set the list mode for the model')
parser.add_argument('-b', '--block', action='store_false', default=True, dest='enabled', help='will add the model as blocked so she will not be recorded even if auto recording conditions are met')
parser.add_argument('-p', '--priority', dest='priority', type=int, default=False, help='set the priority value for the model')
args = vars(parser.parse_args())
try:
    id = str(args['model'][0])
except:
    parser.print_help()
    print()
    parser.print_usage()
    exit()
kwargs = {}
conf = classes.config.Config(os.path.join(sys.path[0], 'config.conf'))

for arg in args.keys():
    if args[arg] and arg is not 'model': kwargs[arg] = args[arg]
    elif arg in ['enabled', 'stop_viewers', 'min_viewers']: kwargs[arg] = args[arg]

def run(id):
    async def run(loop, id):
        client = Client(loop)
        await client.connect(False)
        try:
            id = int(id)
        except ValueError:
            pass
        try:
            msg = await client.query_user(id)
            if msg != None:
                if msg['uid'] not in conf.filter.wanted.dict.keys():
                    new = True
                else:
                    new = False
                    current = conf.filter.wanted.dict[msg['uid']]
                    for key in set(current.keys()) - set(kwargs.keys()):
                        kwargs[key] = current[key]
                if 'custom_name' not in kwargs.keys(): kwargs['custom_name'] = msg['nm']
                conf.filter.wanted._set_data(msg['uid'], **kwargs)
                print("model {} with uid {} added to list".format(msg['nm'], msg['uid'])) if new else\
                print("model {} with uid {} has been updated".format(msg['nm'], msg['uid']))
        except:
            print('something went wrong, model was not added')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop, id))
if __name__ == '__main__':
    run(id)
