import os
from wand.image import Image

period = '2014Q3'
remove_ann_watermark = True
w = 233
h = 318
ann_watermark_h = 13

# Retina
w *= 2
h *= 2

basepath = 'data/%s/images' % period
targetpath = basepath + '/thumb'
for f in os.listdir(basepath):
    if f[0] == '.' or not f.endswith('.jpg'):
        continue
    print f
    path = basepath + '/' + f
    with Image(filename=path) as img:
        if f.startswith('ann') and remove_ann_watermark:
            img.crop(0, 0, img.size[0], img.size[1] - ann_watermark_h)
        img.transform(resize='%dx%d^' % (w, h))
        tw = img.size[0]
        if tw > w:
            img.crop((tw - w) / 2, 0, width=w, height=h)
        img.save(filename=targetpath + '/' + f)

os.system('jpegoptim --max 40 --totals %s/*.jpg' % targetpath)
