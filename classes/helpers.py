import ast
import os
import io
import logging
import hashlib
import base64
import enum
import requests

def try_eval(val):
    try:
        val = ast.literal_eval(val)
    except (ValueError, SyntaxError):
        #evaluation failed, so we most likely have a string
        pass
    return val

def hash_password(password):
    salt = os.urandom(32)
    return base64.b64encode(_hash_password(password, salt)).decode('ascii')

def _hash_password(password, salt):
    #Technically not secure, because the hash computes too fast.
    #This makes it possible to brute-force. Good enough for this purpose though.
    m = hashlib.sha256()
    m.update(password.encode())
    m.update(salt)
    pw_hash = m.digest()
    return pw_hash + salt

def verify_password(password, hash_):
    hash_ = base64.b64decode(hash_.encode('ascii'))
    salt = hash_[32:]
    return _hash_password(password, salt) == hash_

class Condition(enum.IntEnum):
    WANTED = 0
    TAGS = 1
    VIEWERS = 2
    NEW = 3
    SCORE = 4

def condition_text(condition, text='', upper=False):
    texts = {
        0: 'wanted',
        1: 'tags',
        2: 'viewers',
        3: 'new',
        4: 'score',
    }
    if text:
        return '({})'.format(text)
    condition = texts[condition].upper() if upper else texts[condition]
    return condition

def get_avatar(uid):
    '''returns content type and content as BytesIO or None'''
    URL_TEMPLATE = "http://img.mfcimg.com/photos2/{}/{}/avatar.300x300.jpg"
    return _get_img_from_url(URL_TEMPLATE.format(str(uid)[0:3], uid))

def get_live_thumbnail(uid, camserver):
    '''returns content type and content as BytesIO or None'''
    URL_TEMPLATE = 'https://snap.mfcimg.com/snapimg/{}/320x240/mfc_{}'
    return _get_img_from_url(URL_TEMPLATE.format(camserver - 500, uid + 100_000_000))

def _get_img_from_url(url):
    try:
        response = requests.get(url)
        #returns clear.gif if model was not found
        if response.status_code != 200 or 'clear.gif' in response.url:
            return
        return (response.headers['Content-Type'], io.BytesIO(response.content))
    except:
        logging.exception('error getting avatar')
        return
