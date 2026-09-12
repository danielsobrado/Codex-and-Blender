"""Preserve uploaded source images; build named PNG and WebP web textures."""
import hashlib
import json
import math
import shutil
from pathlib import Path
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
config = yaml.safe_load((ROOT/'config/textures.yaml').read_text())
source, delivery = (ROOT/config[k] for k in ('source_dir','delivery_dir'))
source.mkdir(parents=True, exist_ok=True)
records = []
for spec in config['textures']:
    uploaded = (ROOT/spec['upload_dir'] if spec.get('upload_dir') else delivery)/spec['input']
    original = source/(spec['name']+'.png')
    if not original.exists():
        shutil.copy2(uploaded, original)
    if uploaded.exists():
        assert hashlib.sha256(uploaded.read_bytes()).digest() == hashlib.sha256(original.read_bytes()).digest()
        # A checked byte-identical durable copy exists before removing the upload name.
        uploaded.unlink()
    im = Image.open(original).convert('RGBA' if spec['alpha'] else 'RGB')
    size = (config['size']//2, config['size']) if spec['name']=='agave_leaf' else (config['size'],config['size'])
    im = im.resize(size, Image.Resampling.LANCZOS)
    png = delivery/(spec['name']+'.png')
    webp = delivery/(spec['name']+'.webp')
    im.save(png, optimize=True)
    im.save(webp, quality=config['webp_quality'], method=6)
    if spec.get('feather_edges'):
        feather=spec['feather_edges']
        mask=Image.new('L',size)
        pixels=mask.load()
        for y in range(size[1]):
            wobble=feather['irregularity']*(math.sin(y/size[1]*math.tau*3)+.5*math.sin(y/size[1]*math.tau*7))
            for x in range(size[0]):
                distance=min(x/(size[0]-1),1-x/(size[0]-1))
                t=max(0,min(1,(distance-feather['margin']-wobble)/feather['width']))
                pixels[x,y]=round(255*t*t*(3-2*t))
        edge=im.convert('RGBA')
        edge.putalpha(mask)
        edge.save(delivery/(spec['name']+'_edge.png'),optimize=True)
        edge.save(delivery/(spec['name']+'_edge.webp'),quality=config['webp_quality'],method=6)
    records.append(dict(name=spec['name'], original=spec['input'], source=str(original.relative_to(ROOT)), sha256=hashlib.sha256(original.read_bytes()).hexdigest(), size=size, alpha=spec['alpha'], png_bytes=png.stat().st_size, webp_bytes=webp.stat().st_size))
(delivery/'manifest.json').write_text(json.dumps(records,indent=2))
print(json.dumps({'textures':len(records),'webp_total_bytes':sum(x['webp_bytes'] for x in records)},indent=2))
