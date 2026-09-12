import * as THREE from 'three';
import {createSky} from './sky.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const scene=new THREE.Scene();scene.background=new THREE.Color('#a7c6d1');scene.fog=new THREE.FogExp2('#91b1b7',.018);
scene.add(createSky());
const camera=new THREE.PerspectiveCamera(62,innerWidth/innerHeight,.1,140);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;
renderer.shadowMap.autoUpdate=false;
document.body.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxDistance=45;controls.minDistance=1;controls.maxPolarAngle=Math.PI*.53;
function reference(){camera.position.set(0,2.5,12);controls.target.set(0,4.4,-4);controls.update();}reference();
scene.add(new THREE.HemisphereLight('#d5e9f3','#41452a',1.8));
const sun=new THREE.DirectionalLight('#fff0c6',3);sun.position.set(-8,20,-12);sun.target.position.set(0,0,-3);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-25,right:25,top:25,bottom:-25,near:1,far:70});sun.shadow.normalBias=.035;scene.add(sun,sun.target);
const wind={value:1},time={value:0};let model;
try {
 const gltf=await new GLTFLoader().loadAsync('/assets/coastal_jungle.glb');model=gltf.scene;
 model.traverse(o=>{if(!o.isMesh)return;o.receiveShadow=true;o.castShadow=true;const materials=Array.isArray(o.material)?o.material:[o.material];for(const m of materials){if(m.map){m.map.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());}if(m.name.includes('atlas')){m.alphaTest=.4;m.transparent=false;m.side=THREE.DoubleSide;m.depthWrite=true;}if(m.name.includes('grass')){o.castShadow=false;}if(m.name.includes('atlas')&&!m.userData.wind){m.userData.wind=true;m.onBeforeCompile=shader=>{shader.uniforms.forestTime=time;shader.uniforms.windStrength=wind;shader.vertexShader='uniform float forestTime; uniform float windStrength;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvec3 wp=position;\n#ifdef USE_INSTANCING\nwp=(instanceMatrix*vec4(position,1.0)).xyz;\n#endif\ntransformed.x+=sin(forestTime*1.4+wp.x*.7+wp.z*.6)*0.035*windStrength*min(abs(position.y),1.0);');};}}});
 scene.add(model);renderer.shadowMap.needsUpdate=true;window.forestReady=true;
} catch(e){document.querySelector('#status').textContent='Could not load forest: '+e.message;throw e;}
document.querySelector('#reset').onclick=reference;
document.querySelector('#alternate').onclick=()=>{camera.position.set(2,2.3,5);controls.target.set(-3,4.2,-8);controls.update();};
document.querySelector('#wind').onclick=e=>{wind.value=1-wind.value;e.target.textContent='Wind: '+(wind.value?'on':'off');};
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
let frames=0,last=0;
const status=document.querySelector('#status');
renderer.setAnimationLoop(now=>{
  if(!last) last=now;
  time.value=now*.001;
  controls.update();
  renderer.render(scene,camera);
  frames++;
  const elapsed=now-last;
  if(elapsed>=500){
    const fps=Math.round(frames*1000/elapsed);
    window.forestStats={fps,calls:renderer.info.render.calls,triangles:renderer.info.render.triangles};
    status.textContent=`${fps} fps · ${renderer.info.render.calls} draws`;
    last=now;
    frames=0;
  }
});
