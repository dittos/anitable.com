import hashlib
import random
import time
import redis
from flask import json

REDIS = redis.StrictRedis()

def get_account(user_id):
    result = REDIS.hget('accounts', user_id)
    if result is not None:
        result = json.loads(result)
    return result

def put_account(user_id, account):
    account['updated_at'] = time.time()
    return REDIS.hset('accounts', user_id, json.dumps(account))

def add_favorites(user_id, ids):
    if not ids:
        return
    REDIS.sadd('favs:%s' % user_id, *ids)

def remove_favorite(user_id, id):
    REDIS.srem('favs:%s' % user_id, id)

def get_favorites(user_id):
    return list(REDIS.smembers('favs:%s' % user_id))

def generate_session_id():
    return hashlib.sha1(str(time.time()) + ':' + str(random.random())).hexdigest()

def save_temp_session(value, ttl):
    sid = generate_session_id()
    REDIS.setex('tempsess:%s' % sid, ttl, json.dumps(value))
    return sid

def pop_temp_session(sid):
    key = 'tempsess:%s' % sid
    pipe = REDIS.pipeline()
    pipe.get(key)
    pipe.delete(key)
    value, _ = pipe.execute()
    if not value:
        return None
    return json.loads(value)
