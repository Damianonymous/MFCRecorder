import threading
import asyncio
import requests
import mfcauto

SERVER_CONFIG_URL = 'http://www.myfreecams.com/_js/serverconfig.js'

def get_online_models():
    '''returns a dictionary of all online models in free chat'''
    server_config = requests.get(SERVER_CONFIG_URL).json()
    servers = server_config['h5video_servers'].keys()
    models = {}

    def on_tags():
        '''function for the TAGS event in mfcclient'''
        nonlocal models

        try:
            all_results = mfcauto.Model.find_models(lambda m: True)
            models = {int(model.uid): Model(model) for model in all_results
                      if model.uid > 0 and model.bestsession['vs'] == mfcauto.STATE.FreeChat
                      and str(model.bestsession['camserv']) in servers}

            print('{} models online'.format(len(models)))
            client.disconnect()
        except Exception as e:
            print(e)

    #setting a new event loop, because it gets closed in the mfcauo client (feels dirty)
    asyncio.set_event_loop(asyncio.new_event_loop())
    #we dont want to query the models in CLIENT_MODELSLOADED, because we are
    #missing the tags at this point. Rather query everything on TAGS
    client = mfcauto.SimpleClient()
    client.on(mfcauto.FCTYPE.CLIENT_TAGSLOADED, on_tags)

    #put the blocking connect call into another thread in case the loop becomes unresponsive
    t = threading.Thread(target=client.connect)
    t.start()
    #wait up to a minute for the model list from mfcauto
    t.join(60)
    if t.is_alive():
        print("fetching online model list timed out")

    return models

def get_model(uid_or_name):
    '''returns a tuple with uid and name'''
    async def query(loop):
        client = mfcauto.Client(loop)
        await client.connect(False)
        msg = await client.query_user(uid_or_name)
        client.disconnect()
        return msg
    
    #asyncio in a threaded environment...
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    msg = loop.run_until_complete(query(loop))
    return msg if msg is None else (msg['uid'], msg['nm'])

class Model():
    '''custom Model class to preserve the session information'''
    def __init__(self, model):
        self.name = model.nm
        self.uid = model.uid
        self.tags = model.tags
        #vs info will be lost
        self.session = model.bestsession

    def __repr__(self):
        return '{{"name": {}, "uid": {}, "tags": {}, "session": {}}}'.format(
            self.name, self.uid, self.tags, self.session)
