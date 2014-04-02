import time
import json
import redis

REDIS = redis.StrictRedis()

def get_account(user_id):
    result = REDIS.hget('accounts', user_id)
    if result is not None:
        result = json.loads(result)
    return result

def put_account(user_id, account):
    account['updated_at'] = time.time()
    return REDIS.hset('accounts', user_id, json.dumps(account))
