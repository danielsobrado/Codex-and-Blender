import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS,EXTMeshoptCompression} from '@gltf-transform/extensions';
import {weld,reorder} from '@gltf-transform/functions';
import {MeshoptEncoder,MeshoptDecoder} from 'meshoptimizer';
import sharp from 'sharp';
import {build} from 'esbuild';
import {readFile,writeFile,mkdir,readdir,copyFile,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {brotliCompressSync,constants} from 'node:zlib';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'output/browser'), forest=path.join(root,'output/forest');
const config=JSON.parse(await readFile(path.join(root,'config/browser_optimization.yaml'),'utf8'));
await Promise.all(['assets/objects','textures','objects'].map(p=>mkdir(path.join(out,p),{recursive:true})));
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const cache=new Map(), records=[];
const hash=data=>createHash('sha256').update(data).digest('hex').slice(0,20);
const names=(await readdir(path.join(forest,'objects'))).filter(n=>n.endsWith('.glb')).sort();
for(const name of ['coastal_jungle.glb',...names]) {
  const source=path.join(forest,name==='coastal_jungle.glb'?name:`objects/${name}`);
  const doc=await io.read(source);
  const before=doc.getRoot().listMeshes().map(m=>({name:m.getName(),triangles:m.listPrimitives().reduce((s,p)=>s+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0)}));
  for(const texture of doc.getRoot().listTextures()) {
    const image=texture.getImage(), key=hash(image);
    if(!cache.has(key)) {
      const size=/bark|ground|path|skin/i.test(texture.getName())?config.surface_max_size:config.texture_max_size;
      const data=await sharp(image).resize({width:size,height:size,fit:'inside',withoutEnlargement:true}).webp({quality:config.webp_quality,alphaQuality:config.webp_alpha_quality,effort:6}).toBuffer();
      cache.set(key,data);
    }
    const data=cache.get(key);
    texture.setImage(data).setMimeType('image/webp').setURI(`textures/${hash(data)}.webp`);
  }
  // Retain full position/normal precision and node transforms: the runtime builds its own instances.
  await doc.transform(weld(),reorder({encoder:MeshoptEncoder,target:'size'}));
  doc.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({method:EXTMeshoptCompression.EncoderMethod.QUANTIZE});
  const binary=await io.writeBinary(doc);
  if(name!=='coastal_jungle.glb') await writeFile(path.join(out,'objects',name),binary);
  const jsonDoc=await io.writeJSON(doc);
  const assetDir=name==='coastal_jungle.glb'?'assets':'assets/objects';
  const stem=name.replace('.glb','');
  for(const [uri,data] of Object.entries(jsonDoc.resources)) {
    const filename=hash(data)+(uri.endsWith('.webp')?'.webp':'.bin');
    await writeFile(path.join(out,'textures',filename),data);
    const relative=path.posix.relative(assetDir,`textures/${filename}`);
    for(const item of [...(jsonDoc.json.buffers??[]),...(jsonDoc.json.images??[])])if(item.uri===uri)item.uri=relative;
  }
  await writeFile(path.join(out,assetDir,`${stem}.gltf`),JSON.stringify(jsonDoc.json));
  const decoded=await io.readBinary(binary);
  const after=decoded.getRoot().listMeshes().map(m=>({name:m.getName(),triangles:m.listPrimitives().reduce((s,p)=>s+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0)}));
  if(JSON.stringify(before)!==JSON.stringify(after))throw Error(`Mesh names or triangle counts changed: ${name}`);
  records.push({name,sourceBytes:(await stat(source)).size,optimizedGlbBytes:binary.length,meshes:after.length});
}
// Include every texture, even those belonging to the separate dry vegetation kit.
for(const name of (await readdir(path.join(root,'output/textures'))).filter(n=>n.endsWith('.webp'))) {
  const size=/bark|ground|path|skin/i.test(name)?config.surface_max_size:config.texture_max_size;
  await sharp(path.join(root,'output/textures',name)).resize({width:size,height:size,fit:'inside',withoutEnlargement:true}).webp({quality:config.webp_quality,alphaQuality:100,effort:6}).toFile(path.join(out,'textures',name));
}
await copyFile(path.join(forest,'world_config.json'),path.join(out,'assets/world_config.json'));
await copyFile(path.join(forest,'objects/manifest.json'),path.join(out,'objects/manifest.json'));
await build({entryPoints:[path.join(root,'web/main.js')],outfile:path.join(out,'app.js'),bundle:true,minify:true,format:'esm',target:'es2022',legalComments:'eof',define:{FOREST_OPTIMIZED:'true'}});
const html=(await readFile(path.join(root,'web/index.html'),'utf8')).replace(/<script type="importmap">[\s\S]*?<\/script>/,'').replace('src="/main.js"','src="/app.js"');
await writeFile(path.join(out,'index.html'),html);
await copyFile(path.join(root,'web/serve-build.mjs'),path.join(out,'serve.mjs'));
for(const dir of [out,path.join(out,'assets'),path.join(out,'assets/objects'),path.join(out,'textures')])for(const name of await readdir(dir)) {
  if(!/\.(js|html|json|gltf|bin)$/.test(name))continue;
  const data=await readFile(path.join(dir,name));
  await writeFile(path.join(dir,name+'.br'),brotliCompressSync(data,{params:{[constants.BROTLI_PARAM_QUALITY]:config.brotli_quality}}));
}
await writeFile(path.join(out,'optimization_report.json'),JSON.stringify({passed:true,config,assets:records,sourceBytes:records.reduce((s,r)=>s+r.sourceBytes,0),optimizedGlbBytes:records.reduce((s,r)=>s+r.optimizedGlbBytes,0)},null,2));
console.log('Optimized',records.length,'models into',out);
