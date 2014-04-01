import hashlib
import yaml

path = 'data/2014Q2/schedule.yml'
data = list(yaml.load_all(open(path)))

ids = set()

for item in data:
    if 'id' not in item:
        ann_id = item.get('ann_id')
        if ann_id:
            item['id'] = hashlib.sha1('ann%d' % ann_id).hexdigest()[:8]
        else:
            item['id'] = hashlib.sha1('t%s' % item['title']['en']).hexdigest()[:8]

    if item['id'] in ids:
        print 'Error: duplicate id %s (%r)' % (item['id'], item)
        break

    ids.add(item['id'])

with open(path, 'w') as fp:
    yaml.dump_all(data, fp, allow_unicode=True, default_flow_style=False)
