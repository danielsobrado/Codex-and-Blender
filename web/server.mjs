import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const routes={'/assets/':path.resolve(root,'../output/forest'),'/textures/':path.resolve(root,'../output/textures')};
http.createServer(async(req,res)=>{
  try {
    const url=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const prefix=Object.keys(routes).find(p=>url.startsWith(p));
    const base=prefix?routes[prefix]:root;
    const file=path.resolve(base,prefix?url.slice(prefix.length):(url==='/'?'index.html':url.slice(1)));
    if(!file.startsWith(base+path.sep)) {res.writeHead(403).end();return;}
    const data=await readFile(file);
    const type={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.glb':'model/gltf-binary','.json':'application/json','.png':'image/png','.webp':'image/webp'}[path.extname(file)]||'application/octet-stream';
    res.writeHead(200,{'Content-Type':type});res.end(data);
  } catch {res.writeHead(404).end('File not found');}
}).listen(4173,'127.0.0.1',()=>console.log('Coastal jungle: http://127.0.0.1:4173'));
