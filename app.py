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

@app.route('/')
def index():
    return flask.redirect(flask.url_for('schedule', period='2014Q2'))

@app.route('/<period:period>')
def schedule(period):
    path = 'data/%s/schedule.yml' % period
    if not os.path.exists(path):
        flask.abort(404)
    with open(path) as fp:
        data = list(yaml.load_all(fp))
    data.sort(key=lambda item: item['schedule'][0])
    return flask.render_template('index.html', data=data)

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

@app.route('/login')
def login():
    callback_url = flask.url_for('login_complete', popup=flask.request.args.get('popup'))
    return twitter.authorize(callback_url)

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

    if flask.request.args.get('popup') == 'yes':
        js = 'opener.onTwitterConnect(true); window.close()'
        rv = flask.make_response('<script>%s</script>' % js)
        rv.mimetype = 'text/html'
        return rv
    else:
        return flask.redirect('/')

@app.route('/logout')
def logout():
    del flask.session['user_id']
    return flask.redirect('/')

@app.template_filter()
def format_date(s):
    date, time = s.split(' ')
    m, d = map(int, date.split('-'))
    today = datetime.date.today()
    date = datetime.date(today.year, m, d)
    weekday = u'월화수목금토일'[date.weekday()]
    return u'%d/%d (%s)' % (m, d, weekday)

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
def thumb_url(path):
    return flask.url_for('media', path='2014Q2/images/thumb/%s' % path)

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

if __name__ == '__main__':
    app.run(debug=True)
