from pathlib import Path
import json,re,base64,hashlib,runpy,subprocess,tempfile,zipfile,posixpath,sys
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]
def main():
 b=runpy.run_path(str(R/'qa/build.py'));html=(Path(sys.argv[1]) if len(sys.argv)>1 else R/'index.html').read_text();s=BeautifulSoup(html,'html.parser')
 assert s.html['lang']=='sv' and s.select_one('meta[name=viewport]') and s.select_one('main#main')
 assert len(s.select('h1'))==1
 assert not s.select('script[src],link[rel=stylesheet],iframe')
 assert not b['ASSET_RE'].search(html)
 assert all(i['src'].startswith('data:') for i in s.select('img[src]'))
 assert any(a.get_text(strip=True)=='Designed by Ekom' for a in s.select('a[href="https://ekom.se"]'))
 assert not re.search(r'localStorage|sessionStorage|XMLHttpRequest|sendBeacon|\bfetch\s*\(',html)
 assert not re.search(r'url\(\s*[\'"]?https?://',html)
 assert 'info@lundfixar.se' in html and '0722-322 480' in html and 'Romelanda' in html
 assert 'lundfixar@outlook.com' not in html
 script='\n'.join(t.string or '' for t in s.find_all('script'))
 with tempfile.NamedTemporaryFile(mode='w',suffix='.js') as f:
  f.write(script);f.flush();p=subprocess.run(['node','--check',f.name],capture_output=True,text=True);assert p.returncode==0,p.stderr
 inv=b['inventory']();pages=inv['pages'];routes={p['route'] for p in pages};assert len(routes)==len(pages)==23
 valid=routes|set(inv['aliases']);assert set(json.loads((R/'qa/routes.json').read_text()))==routes
 for p in pages:
  soup=BeautifulSoup(p['html'],'html.parser');assert len(soup.select('h1'))==1,p['route']
  ids=[i['id'] for i in soup.select('[id]')];assert len(ids)==len(set(ids)),p['route']
  for a in soup.select('a[href]'):
   h=a['href']
   if h.startswith('#/'):assert h[1:].split('?')[0] in valid,(p['route'],h)
  for i in soup.select('img[src]'):assert (R/i['src']).is_file(),i['src']
  assert not re.search(r'—|\bLorem\b|Jane Doe|Acme',soup.get_text()),p['route']
 manifest=json.loads((R/'qa/assets.json').read_text());assert len(manifest)==75 and len({m['id'] for m in manifest})==75
 media=json.loads((R/'qa/media.json').read_text());assert sum(len(media['gallery-'+str(i)]) for i in range(4))==33
 assert len(media['prints'])==35 and len(media['equipment'])==6
 hashes={hashlib.sha256(base64.b64decode(x,validate=True)).hexdigest() for x in set(re.findall(r'data:[^\s"\'<>;,]+(?:;[^\s"\'<>;,]+)*;base64,([A-Za-z0-9+/=]+)',html))}
 for m in manifest:
  assert hashlib.sha256((R/m['file']).read_bytes()).hexdigest()==m['sha256'],m['file']
  assert m['source_url'].startswith('https://') and m['sha256'] in hashes,m['file']
 for m in json.loads((R/'qa/fonts.json').read_text()):assert m['sha256'] in hashes and hashlib.sha256((R/m['file']).read_bytes()).hexdigest()==m['sha256']
 package=json.loads((R/'qa/package-result.json').read_text());archive=Path(package['archive']);assert hashlib.sha256(archive.read_bytes()).hexdigest()==package['sha256']
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for n in z.namelist():
   if (R/n).is_file():assert z.read(n)==(R/n).read_bytes(),n
   elif n.endswith('/index.html'):
    soup=BeautifulSoup(z.read(n),'html.parser');dest=soup.select_one('a')['href'].split('#')[0];assert posixpath.normpath(posixpath.join(posixpath.dirname(n),dest)) in z.namelist()
 print('SITE_VERIFIED')
if __name__=='__main__':main()
