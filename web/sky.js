import * as THREE from 'three';

export function createSky() {
  return new THREE.Mesh(new THREE.SphereGeometry(300, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    vertexShader: `varying vec3 direction;
      void main() { direction=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `varying vec3 direction;
      float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
      float noise(vec2 p) {
        vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
      }
      float fbm(vec2 p) {
        float n=0.0, a=0.5;
        for(int i=0;i<5;i++) { n+=a*noise(p); p=mat2(1.6,1.2,-1.2,1.6)*p+7.3; a*=0.5; }
        return n;
      }
      void main() {
        vec3 d=normalize(direction);
        float h=smoothstep(0.0,0.85,d.y);
        vec3 color=mix(vec3(0.68,0.79,0.82),vec3(0.17,0.37,0.61),h);
        vec2 q=d.xz/max(d.y+0.2,0.15);
        float clouds=smoothstep(0.48,0.70,fbm(q*3.0));
        color=mix(color,vec3(0.93,0.93,0.88),clouds*smoothstep(0.02,0.18,d.y)*0.8);
        gl_FragColor=vec4(color,1.0);
      }`
  }));
}
