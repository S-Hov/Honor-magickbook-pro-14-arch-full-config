import json,urllib.request,pathlib,concurrent.futures,hashlib
root=pathlib.Path.home()/'.local/share/honor-dictation/model';root.mkdir(parents=True,exist_ok=True)
info=json.loads((pathlib.Path(__file__).parent/'model.json').read_text());info['id']=info['repository'];rev=info['revision']
files=json.load(urllib.request.urlopen('https://huggingface.co/api/models/OpenVINO/whisper-small-int8-ov/tree/'+rev+'?recursive=true'))
def download(item):
 if item['type']!='file' or item['path']=='.gitattributes':return
 p=root/item['path'];p.parent.mkdir(parents=True,exist_ok=True)
 digest=item.get('lfs',{}).get('oid')
 if p.exists() and p.stat().st_size==item['size'] and (not digest or hashlib.sha256(p.read_bytes()).hexdigest()==digest):return
 tmp=p.with_suffix(p.suffix+'.download')
 request=urllib.request.Request('https://huggingface.co/OpenVINO/whisper-small-int8-ov/resolve/'+rev+'/'+item['path'],headers={'User-Agent':'honor-local-dictation'})
 with urllib.request.urlopen(request,timeout=90) as r,tmp.open('wb') as f:
  while chunk:=r.read(1024*1024):f.write(chunk)
 assert tmp.stat().st_size==item['size'],item['path']
 if digest:assert hashlib.sha256(tmp.read_bytes()).hexdigest()==digest,item['path']
 tmp.replace(p);print(item['path'],item['size'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,files))
(root/'honor-source.json').write_text(json.dumps({'repository':info['id'],'revision':rev},indent=2)+'\n')
print('Download complete',rev)
