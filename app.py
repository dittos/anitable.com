# -*- coding: utf-8 -*-
import datetime
import itertools
import os
import time
import urllib
import flask
import yaml
import db
from werkzeug.routing import BaseConverter
from flask_oauthlib.client import OAuth

app = flask.Flask(__name__)
app.config['THUMB_SIZE'] = (233, 318)
app.config.from_pyfile('config.py')

oauth = OAuth(app)
twitter = oauth.remote_app(
    'twitter',
    consumer_key=app.config['TWITTER_CONSUMER_CREDENTIAL'][0],
    consumer_secret=app.config['TWITTER_CONSUMER_CREDENTIAL'][1],
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
)

@twitter.tokengetter
def get_twitter_token():
    if flask.g.account:
        resp = flask.g.account
        return resp['oauth_token'], resp['oauth_token_secret']

class PeriodConverter(BaseConverter):
    regex = '[0-9]{4}Q[1-4]'

app.url_map.converters['period'] = PeriodConverter

def require_login():
    if not flask.g.account:
        flask.abort(403)

def next_schedule(date):
    day = datetime.timedelta(days=1)
    thres = datetime.timedelta(hours=12)
    while date + thres < datetime.datetime.now():
        date = date + 7 * day
    return date

def get_schedule(item):
    if 'schedule' not in item:
        return None
    return item['schedule'][0]

def get_schedule_kr(item):
    if len(item.get('schedule_kr', [])) != 2:
        return None
    return item['schedule_kr'][0]

def process_item(item, period):
    if 'schedule' in item:
        date = next_schedule(parse_date(item['schedule'][0]))
        item['schedule'][0] = date.strftime('%m-%d %H:%M')
    date_kr = get_schedule_kr(item)
    if date_kr:
        date_kr = next_schedule(parse_date(date_kr))
        item['schedule_kr'][0] = date_kr.strftime('%m-%d %H:%M')
    if isinstance(item['title'], basestring):
        item['title'] = {'ko': item['title']}
    if 'image' in item:
        item['thumb_url'] = flask.url_for('media', path='%s/images/thumb/%s' % (period, item['image']))

def nullslast(key):
    return (key is None, key)

@app.route('/')
def index():
    return flask.redirect(flask.url_for('schedule', period='2014Q3'))

@app.route('/<period:period>')
def schedule(period):
    if app.config.get('ANIMETABLE'):
        return flask.redirect('http://animeta.net/table/%s/' % period)

    path = 'data/%s/schedule.yml' % period
    if not os.path.exists(path):
        flask.abort(404)

    if flask.g.account:
        favs = db.get_favorites(flask.g.user_id)
        settings = db.get_settings(flask.g.user_id)
    else:
        favs = []
        settings = {'preferKR': flask.request.args.get('preferKR') == 'true'}
    
    with open(path) as fp:
        data = list(yaml.load_all(fp))
    for item in data:
        process_item(item, period)
    
    if settings.get('preferKR'):
        data.sort(key=lambda item: nullslast(get_schedule_kr(item) or get_schedule(item)))
    else:
        data.sort(key=lambda item: nullslast(get_schedule(item)))

    return flask.render_template('index.html', period=period, data=data, favs=favs, settings=settings)

@app.route('/media/<path:path>')
def media(path):
    return flask.send_from_directory('data', path)

@app.before_request
def load_account():
    user_id = flask.session.get('user_id')
    account = None
    if user_id:
        account = db.get_account(user_id)
    flask.g.account = account or {}
    flask.g.user_id = user_id

@app.route('/login')
def login():
    callback_url = flask.url_for('login_complete')
    return twitter.authorize(callback_url)

@app.route('/save', methods=['POST'])
def save():
    ids = flask.request.form.getlist('ids[]')
    if flask.g.account:
        db.add_favorites(flask.g.user_id, ids)
        return flask.redirect('/')
    else:
        flask.session['temp_session_id'] = db.save_temp_session(ids, 60 * 60) # 1 hour
        return login()

@app.route('/login/complete')
@twitter.authorized_handler
def login_complete(resp):
    if resp is None:
        return flask.redirect('/')
    user_id = resp['user_id']
    account = db.get_account(user_id)
    if not account:
        account = resp
        account['created_at'] = time.time()
    db.put_account(user_id, account)
    flask.session['user_id'] = user_id
    sid = flask.session.pop('temp_session_id', default=None)
    if sid:
        ids = db.pop_temp_session(sid)
        db.add_favorites(user_id, ids)
        flask.flash(u'환영합니다! 선택하신 작품 %d개가 관심 체크 됐습니다.' % len(ids))
    return flask.redirect('/')

@app.route('/logout')
def logout():
    del flask.session['user_id']
    return flask.redirect('/')

@app.route('/fav', methods=['POST'])
def add_favorite():
    require_login()
    db.add_favorites(flask.g.user_id, [flask.request.form['id']])
    return flask.jsonify(ok=True)

@app.route('/fav/remove', methods=['POST'])
def remove_favorite():
    require_login()
    db.remove_favorite(flask.g.user_id, flask.request.form['id'])
    return flask.jsonify(ok=True)

@app.route('/settings', methods=['POST'])
def save_settings():
    require_login()
    db.save_settings(flask.g.user_id, flask.request.get_json())
    return flask.jsonify(ok=True)

def parse_date(s):
    date, time = s.split(' ')
    m, d = map(int, date.split('-'))
    today = datetime.date.today()
    h, min = map(int, time.split(':'))
    return datetime.datetime(today.year, m, d, h, min)

@app.template_filter()
def format_date(s):
    date = parse_date(s)
    weekday = u'월화수목금토일'[date.weekday()]
    return u'%s (%s)' % (date.strftime('%m/%d'), weekday)

@app.template_filter()
def format_time(s):
    date, time = s.split(' ')
    h, m = map(int, time.split(':'))
    result = u''
    if h < 12:
        result += u'오전 %d시' % h
    elif h == 12:
        result += u'정오'
    else:
        result += u'오후 %d시' % (h - 12)
    if m > 0:
        result += u' %02d분' % m
    return result

@app.template_filter()
def multiple(s):
    if isinstance(s, basestring):
        s = [s]
    return u', '.join(s)

@app.template_filter()
def is_undetermined_schedule(s):
    return isinstance(s, basestring)

SOURCE_TYPE_MAP = {
    'manga': u'만화 원작', 
    'original': u'오리지널',
    'lightnovel': u'라노베 원작',
    'game': u'게임 원작',
    '4koma': u'4컷 만화 원작',
    'visualnovel': u'비주얼 노벨 원작',
    'novel': u'소설 원작',
}

@app.template_filter()
def source_readable(s):
    return SOURCE_TYPE_MAP.get(s, '')

@app.template_filter()
def enha_link(ref):
    t = ref.rsplit('#', 1)
    if len(t) == 2:
        page, anchor = t
    else:
        page = ref
        anchor = None
    url = 'http://mirror.enha.kr/wiki/' + urllib.quote(page.encode('utf-8'))
    if anchor:
        url += '#' + urllib.quote(anchor.encode('utf-8'))
    return url

QUARTERS = 1, 4, 7, 10

@app.template_filter()
def period_readable(p):
    year, quarter = p.split('Q')
    return u'%s년 %s월' % (year, QUARTERS[int(quarter) - 1])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
