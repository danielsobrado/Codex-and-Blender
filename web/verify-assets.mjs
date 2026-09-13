import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {MeshoptDecoder} from 'meshoptimizer';
import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const hash=data=>createHash('sha256').update(data).digest('hex');
function signature(doc) {
  return {
    meshes:doc.getRoot().listMeshes().map(mesh=>({name:mesh.getName(),primitives:mesh.listPrimitives().map(p=>{
      const semantics=p.listSemantics().sort(),attributes=semantics.map(s=>p.getAttribute(s));
      const vertices=new Set();
      for(let i=0;i<attributes[0].getCount();i++)vertices.add(attributes.map(a=>{
        const array=a.getArray(),n=a.getElementSize();
        return Array.from(array.subarray(i*n,(i+1)*n)).join(',');
      }).join('|'));
      return {semantics,vertices:hash([...vertices].sort().join(';')),indices:p.getIndices()?.getCount(),material:p.getMaterial()?.getName()};
    })})),
    nodes:doc.getRoot().listNodes().map(n=>({name:n.getName(),matrix:n.getMatrix(),mesh:n.getMesh()?.getName(),instances:n.getExtension('EXT_mesh_gpu_instancing')?.listAttributes().map(a=>hash(Buffer.from(a.getArray().buffer,a.getArray().byteOffset,a.getArray().byteLength)))})),
    materials:doc.getRoot().listMaterials().map(m=>({name:m.getName(),color:m.getBaseColorFactor(),alpha:m.getAlphaMode(),cutoff:m.getAlphaCutoff(),doubleSided:m.getDoubleSided()}))
  };
}
const report=JSON.parse(await readFile('../output/browser/optimization_report.json','utf8'));
for(const record of report.assets) {
  const source=`../output/forest/${record.name==='coastal_jungle.glb'?'':'objects/'}${record.name}`;
  const target=`../output/browser/${record.name==='coastal_jungle.glb'?'assets/coastal_jungle.gltf':'objects/'+record.name}`;
  const original=signature(await io.read(source)), optimized=signature(await io.read(target));
  if(JSON.stringify(original)!==JSON.stringify(optimized))throw Error(`Geometry, transforms or material mismatch: ${record.name}`);
  record.sourceSHA256=hash(await readFile(source));
  record.verified=true;
}
report.passed=true;
await writeFile('../output/browser/asset_validation.json',JSON.stringify(report,null,2));
console.log('Exact vertex attributes, transforms, instance arrays and materials preserved for',report.assets.length,'models.');
