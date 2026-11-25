import json,re,base64,hashlib,mimetypes,subprocess,zipfile,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSET_RE=re.compile(r'(?<![A-Za-z0-9_./:\-])(?:assets|fonts)/[A-Za-z0-9_./\-]+\.(?:webp|png|jpg|jpeg|avif|woff2|ttf)(?![A-Za-z0-9_.\-])')
def read(n):return (ROOT/n).read_text()
def jsjson(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
def prefix():return 'const CONTENT='+jsjson(json.loads(read('qa/content.json')))+';\nconst MEDIA='+jsjson(json.loads(read('qa/media.json')))+';\n'
def pure():return read('qa/site.js').split('//__BROWSER__')[0]
def node(code):
 p=subprocess.run(['node'],input=code,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout
def inventory():return json.loads(node(prefix()+pure()+"\nprocess.stdout.write(JSON.stringify({pages:entries().map(p=>({route:p.route,title:p.title,html:p.render()})),aliases:ALIASES}));"))
def build():
 inv=inventory();home=next(p['html'] for p in inv['pages'] if p['route']=='/');m=json.loads(read('qa/media.json'))['logo'];logo=f'<img src="{m["file"]}" width="{m["width"]}" height="{m["height"]}" alt="Lund Fixar">'
 editable=read('qa/template.html').replace('<!--__LOGO__-->',logo).replace('<!--__HOME__-->',home).replace('/*__CSS__*/',read('qa/site.css')).replace('/*__DATA__*/',prefix()).replace('/*__JS__*/',read('qa/site.js'))
 assert '/*__' not in editable
 (ROOT/'redigerbar.html').write_text(editable)
 used=sorted(set(ASSET_RE.findall(editable)));data={f:'data:'+(mimetypes.guess_type(f)[0] or 'application/octet-stream')+';base64,'+base64.b64encode((ROOT/f).read_bytes()).decode() for f in used}
 standalone=ASSET_RE.sub(lambda m:data[m[0]],editable);assert not ASSET_RE.search(standalone)
 (ROOT/'index.html').write_text(standalone)
 routes=[p['route'] for p in inv['pages']];(ROOT/'qa/routes.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2))
 fonts=[dict(file='fonts/dm-sans.woff2',family='DM Sans',weight='100-1000',source_url='https://fonts.gstatic.com/s/dmsans/v17/rP2Yp2ywxg089UriI5-g4vlH9VoD8Cmcqbu0-K4.woff2',license='SIL Open Font License')]
 for f in fonts:f['sha256']=hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest()
 (ROOT/'qa/fonts.json').write_text(json.dumps(fonts,indent=2))
 fixed=['index.html','redigerbar.html','LAS-MIG.md','qa/build.py','qa/check.py','qa/site.css','qa/site.js','qa/template.html','qa/content.json','qa/media.json','qa/routes.json','qa/assets.json','qa/facts.json','qa/fonts.json','qa/DESIGN.md','research/SOURCES.md','research/pages-manifest.json','fonts/DM-Sans-LICENSE.txt']
 fixed += [str(p.relative_to(ROOT)) for p in (ROOT/'research/pages').glob('*.html')]
 redirects={r:r for r in routes if r!='/'}|inv['aliases']
 archive=ROOT/'package.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for f in fixed+used:z.write(ROOT/f,f)
  for old,target in sorted(redirects.items()):
   path=old.strip('/');url='../'*len(path.split('/'))+'redigerbar.html#'+target
   z.writestr(path+'/index.html',f'<!doctype html><html lang="sv"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url={html.escape(url,quote=True)}"><title>Lund Fixar</title><a href="{html.escape(url,quote=True)}">Fortsätt</a></html>')
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for f in fixed+used:assert z.read(f)==(ROOT/f).read_bytes(),f
 result=dict(archive=str(archive),archive_bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),entries=len(z.namelist()),standalone_bytes=(ROOT/'index.html').stat().st_size,editable_bytes=(ROOT/'redigerbar.html').stat().st_size,used_assets=len(used),routes=len(routes),redirects=len(redirects),crc='pass',files_match='pass')
 (ROOT/'qa/package-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':build()
