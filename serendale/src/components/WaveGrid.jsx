// src/components/WaveGrid.jsx
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useMemo, useRef } from 'react'

// GLSL helpers: value noise (fast) for displacement
const vertexShader = `
  uniform float uTime;
  uniform float uFreq;
  uniform float uTilt;      // slope left->right
  uniform float uLargeAmp;  // amplitude for large waves
  varying vec2 vUv;

  float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453123); }
  float noise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f*f*(3.0-2.0*f);
    return mix(a, b, u.x) + (c - a)*u.y*(1.0 - u.x) + (d - b)*u.x*u.y;
  }

  void main() {
    vUv = uv;
    vec3 pos = position;
    // layered noise for richer displacement
    float n = 0.0;
    n += noise(uv * uFreq + vec2(uTime*0.15, uTime*0.10))*0.6;
    n += noise(uv * (uFreq*0.5) + vec2(-uTime*0.07, uTime*0.05))*0.4;
    pos.z += (n - 0.5) * 10.0; // elevate by noise
    // add large, smooth band waves so it doesn't look flat
    float band = sin((uv.x*3.2 + uTime*0.2) * 3.14159) * 0.5 + sin((uv.y*2.6 - uTime*0.16) * 3.14159) * 0.5;
    pos.z += band * uLargeAmp;
    // global tilt: left lower, right higher
    pos.z += (uv.x - 0.5) * uTilt;
    // tilt plane slightly for slanted perspective
    pos = vec3(pos.x, pos.y, pos.z);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`

// Draw grid lines in fragment shader to simulate wireframe and color with gradient
const fragmentShader = `
  precision mediump float;
  uniform float uTime;
  uniform vec3 uColorA;
  uniform vec3 uColorB;
  uniform float uGridScale;
  uniform float uLineWidth;
  varying vec2 vUv;

  mat2 rot(float a){ float c = cos(a), s = sin(a); return mat2(c,-s,s,c); }

  // Return 1.0 on grid lines, 0.0 elsewhere
  float grid(vec2 uv, float scale, float width){
    // rotate UV to slant the grid
    vec2 suv = (uv - 0.5);
    suv = rot(0.28) * suv; // a bit more slanted
    suv += 0.5;
    vec2 g = abs(fract(suv * scale) - 0.5);
    float d = min(g.x, g.y);
    return smoothstep(width, 0.0, d);
  }

  void main(){
    // gradient across X
    float t = clamp(vUv.x, 0.0, 1.0);
    vec3 base = mix(uColorA, uColorB, t);
    float lines = grid(vUv + vec2(0.0, 0.18), uGridScale, uLineWidth);
    float alpha = lines; // show only lines
    vec3 color = base;
    gl_FragColor = vec4(color, alpha);
  }
`

function ProceduralMesh() {
  const mat = useRef()

  const shaderMat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uFreq: { value: 5.5 },
      uGridScale: { value: 104 },
      uLineWidth: { value: 0.030 },
      uColorA: { value: new THREE.Color('#df16e2') }, // purple
      uColorB: { value: new THREE.Color('#22d3ee') }, // cyan
      uTilt: { value: 26.0 },
      uLargeAmp: { value: 3.8 },
    },
    vertexShader,
    fragmentShader,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  }), [])

  useFrame(({ clock }) => {
    shaderMat.uniforms.uTime.value = clock.getElapsedTime()
  })

  return (
    <mesh rotation={[-Math.PI / 2.08, 0.24, -0.08]} position={[0, -12, 0]}>
      <planeGeometry args={[820, 260, 360, 360]} />
      <primitive object={shaderMat} ref={mat} attach="material" />
    </mesh>
  )
}

export default function WaveGrid() {
  // Bottom overlay, slightly higher placement
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, width: '100vw', height: '58vh', pointerEvents: 'none', zIndex: 0 }}>
      <Canvas gl={{ antialias: true, alpha: true }} camera={{ position: [0, 24, 84], fov: 60 }}>
        <ProceduralMesh />
      </Canvas>
    </div>
  )
}
