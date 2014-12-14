import hashlib
import yaml

period = '2015Q1'
path = 'data/%s/schedule.yml' % period
data = list(yaml.load_all(open(path)))

ids = []

for item in data:
    id = item.get('id')
    if not id:
        ann_id = item.get('ann_id')
        if ann_id:
            id = hashlib.sha1('ann%d' % ann_id).hexdigest()[:8]
        else:
            title = item['title']
            if isinstance(title, dict):
                title = title['en']
            id = hashlib.sha1('t%s' % title.encode('utf-8')).hexdigest()[:8]

    if id in ids:
        print 'Error: duplicate id %s (%r)' % (item['id'], item)
        break

    ids.append(id)

data = open(path).read()
if data.startswith('---'):
    data = data[len('---'):]
data = data.split('\n---')
for i, item in enumerate(data):
    print '---'
    print 'id: ' + ids[i]
    print item.strip()
