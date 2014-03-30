# -*- coding: utf-8 -*-
import datetime
import itertools
import os
import urllib
import flask
import yaml
from werkzeug.routing import BaseConverter

app = flask.Flask(__name__)
app.config['THUMB_SIZE'] = (233, 318)

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
