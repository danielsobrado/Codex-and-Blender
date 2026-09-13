import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=process.env.FOREST_DIST||path.dirname(fileURLToPath(import.meta.url));
http.createServer(async(req,res)=>{
  try {
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(root,pathname==='/'?'index.html':pathname.slice(1));
    if(!file.startsWith(path.resolve(root)+path.sep)){res.writeHead(403).end();return;}
    let data,encoding;
    if(/\bbr\b/.test(req.headers['accept-encoding']||''))try{data=await readFile(file+'.br');encoding='br';}catch{}
    data??=await readFile(file);
    const type={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.gltf':'model/gltf+json','.json':'application/json','.webp':'image/webp'}[path.extname(file)]||'application/octet-stream';
    const headers={'Content-Type':type,'Content-Length':data.length,'Vary':'Accept-Encoding','Cache-Control':/[a-f0-9]{20}\./.test(file)?'public, max-age=31536000, immutable':'no-cache'};
    if(encoding)headers['Content-Encoding']=encoding;
    res.writeHead(200,headers).end(data);
  }catch{res.writeHead(404).end('File not found');}
}).listen(Number(process.env.PORT||4174),'127.0.0.1',()=>console.log('Optimized forest: http://127.0.0.1:'+(process.env.PORT||4174)));
