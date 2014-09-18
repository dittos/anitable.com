import os.path
import urllib
from xml.etree import ElementTree
import requests

basepath = 'data/2014Q4'
path = basepath + '/schedule.yml'
with open(path) as fp:
    data = fp.read().split('\n---')

result = ''
for item in data:
    ann_id = None
    for line in item.splitlines():
        t = line.split(':', 1)
        if len(t) == 2 and t[0] == 'ann_id':
            ann_id = t[1].strip()
            break
    if ann_id:
        fn = 'ann' + str(ann_id) + '.jpg'
        imgpath = basepath + '/images/' + fn
        if not os.path.exists(imgpath):
            info = requests.get('http://cdn.animenewsnetwork.com/encyclopedia/api.xml?anime=' + str(ann_id))
            tree = ElementTree.fromstring(info.content)
            fullsrc = None
            for img in tree.findall('.//info[@type="Picture"]/img'):
                src = img.attrib['src']
                if 'full' in src:
                    fullsrc = src
                elif 'max' in src and not fullsrc:
                    fullsrc = src
            if fullsrc:
                urllib.urlretrieve(fullsrc, imgpath)
        if os.path.exists(imgpath):
            item = item.rstrip() + '\nimage: ' + fn
    result += '---\n' + item.strip() + '\n'

print result
