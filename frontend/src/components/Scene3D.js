import React, { useRef, useMemo, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial, Sphere, Box, Torus, Icosahedron, Octahedron } from '@react-three/drei';
import * as THREE from 'three';

/* ═══════════ HERO — Deep 3D Neural Network ═══════════ */
const NODE_COUNT = 160;
const EDGE_COUNT = 200;

function NetworkNodes() {
  const meshRef = useRef();
  const positions = useMemo(() => {
    const pos = new Float32Array(NODE_COUNT * 3);
    for (let i = 0; i < NODE_COUNT; i++) {
      // Spherische Verteilung für echte 3D-Tiefe
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 2 + Math.random() * 4;
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.6;
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    return pos;
  }, []);

  const sizes = useMemo(() => {
    const s = new Float32Array(NODE_COUNT);
    for (let i = 0; i < NODE_COUNT; i++) {
      s[i] = 0.03 + Math.random() * 0.06;
    }
    return s;
  }, []);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime() * 0.15;
    const posArr = meshRef.current.geometry.attributes.position.array;
    for (let i = 0; i < NODE_COUNT; i++) {
      posArr[i * 3] += Math.sin(t + i * 0.3) * 0.002;
      posArr[i * 3 + 1] += Math.cos(t + i * 0.2) * 0.002;
      posArr[i * 3 + 2] += Math.sin(t * 0.5 + i * 0.15) * 0.001;
    }
    meshRef.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={NODE_COUNT} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.06} color="#ff9b7a" transparent opacity={0.85} sizeAttenuation depthWrite={false} />
    </points>
  );
}

function NetworkEdges() {
  const linesRef = useRef();
  const positions = useMemo(() => {
    const pos = [];
    for (let i = 0; i < EDGE_COUNT; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r1 = 2 + Math.random() * 3.5;
      const x1 = r1 * Math.sin(phi) * Math.cos(theta);
      const y1 = r1 * Math.sin(phi) * Math.sin(theta) * 0.6;
      const z1 = r1 * Math.cos(phi);
      const x2 = x1 + (Math.random() - 0.5) * 2.5;
      const y2 = y1 + (Math.random() - 0.5) * 1.8;
      const z2 = z1 + (Math.random() - 0.5) * 2;
      pos.push(x1, y1, z1, x2, y2, z2);
    }
    return new Float32Array(pos);
  }, []);

  useFrame(({ clock }) => {
    if (linesRef.current) {
      linesRef.current.rotation.y = clock.getElapsedTime() * 0.025;
      linesRef.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.012) * 0.08;
      linesRef.current.rotation.z = Math.cos(clock.getElapsedTime() * 0.008) * 0.03;
    }
  });

  return (
    <lineSegments ref={linesRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={EDGE_COUNT * 2} array={positions} itemSize={3} />
      </bufferGeometry>
      <lineBasicMaterial color="#ff9b7a" transparent opacity={0.12} />
    </lineSegments>
  );
}

function FloatingCore() {
  const groupRef = useRef();
  const outerRef = useRef();
  const innerRef = useRef();
  const shellRef = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (groupRef.current) {
      groupRef.current.rotation.y = t * 0.06;
      groupRef.current.position.y = Math.sin(t * 0.4) * 0.15;
    }
    if (outerRef.current) {
      outerRef.current.rotation.x = t * 0.12;
      outerRef.current.rotation.y = t * 0.18;
      outerRef.current.rotation.z = t * 0.08;
    }
    if (innerRef.current) {
      innerRef.current.rotation.x = t * -0.08;
      innerRef.current.rotation.z = t * 0.1;
    }
    if (shellRef.current) {
      shellRef.current.rotation.y = -t * 0.05;
      shellRef.current.rotation.x = t * 0.03;
    }
  });

  return (
    <group ref={groupRef} position={[1.5, 0, 0]}>
      {/* Outer wireframe shell — visible 3D structure */}
      <group ref={outerRef}>
        <Icosahedron args={[2, 1]}>
          <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.18} />
        </Icosahedron>
      </group>
      {/* Mid shell — counter-rotating for depth */}
      <group ref={shellRef}>
        <Icosahedron args={[1.5, 2]}>
          <meshBasicMaterial color="#ffb59e" wireframe transparent opacity={0.08} />
        </Icosahedron>
      </group>
      {/* Inner distorted sphere */}
      <group ref={innerRef}>
        <Icosahedron args={[1.1, 0]}>
          <MeshDistortMaterial color="#ff9b7a" transparent opacity={0.1} distort={0.4} speed={2} />
        </Icosahedron>
      </group>
      {/* Bright core */}
      <Sphere args={[0.35, 24, 24]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={2} transparent opacity={0.35} />
      </Sphere>
      {/* Core inner glow */}
      <Sphere args={[0.15, 16, 16]}>
        <meshStandardMaterial color="#ffffff" emissive="#ff9b7a" emissiveIntensity={3} transparent opacity={0.6} />
      </Sphere>
      {/* Orbiting ring */}
      <Torus args={[1.8, 0.015, 8, 64]} rotation={[1.2, 0.5, 0]}>
        <meshBasicMaterial color="#ff9b7a" transparent opacity={0.25} />
      </Torus>
      <Torus args={[1.3, 0.01, 8, 48]} rotation={[0.5, 1.5, 0.3]}>
        <meshBasicMaterial color="#ffb59e" transparent opacity={0.15} />
      </Torus>
    </group>
  );
}

function DataStreams() {
  const ref = useRef();
  const count = 600;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 12;
      const radius = 1 + Math.random() * 5;
      const heightSpread = (Math.random() - 0.5) * 8;
      p[i * 3] = Math.cos(angle) * radius;
      p[i * 3 + 1] = heightSpread * 0.6;
      p[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return p;
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.04;
      ref.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.02) * 0.05;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.025} color="#ffb59e" transparent opacity={0.45} sizeAttenuation depthWrite={false} />
    </points>
  );
}

function AccentGeometries() {
  const ref1 = useRef();
  const ref2 = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref1.current) { ref1.current.rotation.x = t * 0.15; ref1.current.rotation.y = t * 0.1; }
    if (ref2.current) { ref2.current.rotation.z = t * 0.12; ref2.current.rotation.x = t * 0.08; }
  });

  return (
    <>
      <Float speed={0.6} rotationIntensity={0.3} floatIntensity={0.4}>
        <Sphere args={[0.18, 16, 16]} position={[4.5, 2.5, -2]}>
          <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={1.2} transparent opacity={0.65} />
        </Sphere>
      </Float>
      <Float speed={0.5} rotationIntensity={0.2} floatIntensity={0.3}>
        <group ref={ref1} position={[-4.5, -2, 1]}>
          <Octahedron args={[0.35, 0]}>
            <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.2} />
          </Octahedron>
        </group>
      </Float>
      <Float speed={0.7} rotationIntensity={0.25} floatIntensity={0.35}>
        <Torus args={[0.35, 0.08, 8, 24]} position={[4.5, -2.5, -1.5]} rotation={[1, 0.5, 0]}>
          <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={0.5} transparent opacity={0.3} />
        </Torus>
      </Float>
      <Float speed={0.4} rotationIntensity={0.15} floatIntensity={0.2}>
        <group ref={ref2} position={[-3.5, 2.5, -1.5]}>
          <Icosahedron args={[0.2, 0]}>
            <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.2} />
          </Icosahedron>
        </group>
      </Float>
      <Float speed={0.8} rotationIntensity={0.3} floatIntensity={0.3}>
        <Sphere args={[0.1, 8, 8]} position={[2.5, -3.5, 0.5]}>
          <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={2} transparent opacity={0.55} />
        </Sphere>
      </Float>
      <Float speed={0.3} rotationIntensity={0.1} floatIntensity={0.2}>
        <Sphere args={[0.08, 8, 8]} position={[-2, -3, 1]}>
          <meshStandardMaterial color="#ffb59e" emissive="#ffb59e" emissiveIntensity={1.5} transparent opacity={0.5} />
        </Sphere>
      </Float>
    </>
  );
}

export function HeroScene() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      <Canvas
        camera={{ position: [0, 0.5, 7], fov: 55 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <ambientLight intensity={0.35} />
        <pointLight position={[6, 4, 6]} intensity={0.8} color="#ff9b7a" distance={25} decay={2} />
        <pointLight position={[-5, -3, 4]} intensity={0.4} color="#ff9b7a" distance={18} decay={2} />
        <pointLight position={[0, -6, 5]} intensity={0.25} color="#ffb59e" distance={15} decay={2} />
        <pointLight position={[3, 5, -2]} intensity={0.2} color="#ff6b4a" distance={12} decay={2} />
        <Suspense fallback={null}>
          <FloatingCore />
          <NetworkNodes />
          <NetworkEdges />
          <DataStreams />
          <AccentGeometries />
        </Suspense>
      </Canvas>
    </div>
  );
}

/* ═══════════ INTEGRATIONS GLOBE — Deep 3D Wireframe ═══════════ */
function GlobeWireframe() {
  const ref = useRef();
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.06;
      ref.current.rotation.x = 0.25 + Math.sin(clock.getElapsedTime() * 0.02) * 0.05;
    }
  });
  return (
    <group ref={ref}>
      <Sphere args={[2, 32, 32]}>
        <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.12} />
      </Sphere>
      <Sphere args={[2.15, 20, 20]}>
        <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.05} />
      </Sphere>
      {/* Equatorial ring */}
      <Torus args={[2.08, 0.018, 8, 64]} rotation={[Math.PI / 2, 0, 0]}>
        <meshBasicMaterial color="#ff9b7a" transparent opacity={0.3} />
      </Torus>
      {/* Polar ring */}
      <Torus args={[2.08, 0.012, 8, 64]} rotation={[0, 0, 0]}>
        <meshBasicMaterial color="#ff9b7a" transparent opacity={0.15} />
      </Torus>
      {/* Angled ring */}
      <Torus args={[2.08, 0.01, 8, 64]} rotation={[Math.PI / 3, Math.PI / 4, 0]}>
        <meshBasicMaterial color="#ff9b7a" transparent opacity={0.1} />
      </Torus>
      {/* Central glow — much brighter */}
      <Sphere args={[0.25, 16, 16]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={2} transparent opacity={0.4} />
      </Sphere>
    </group>
  );
}

function GlobeNodes() {
  const ref = useRef();
  const count = 120;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 2.08;
      p[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      p[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      p[i * 3 + 2] = r * Math.cos(phi);
    }
    return p;
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.06;
      ref.current.rotation.x = 0.25 + Math.sin(clock.getElapsedTime() * 0.02) * 0.05;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.1} color="#ff9b7a" transparent opacity={0.95} sizeAttenuation />
    </points>
  );
}

function ConnectionArcs() {
  const ref = useRef();
  const arcs = useMemo(() => {
    const lines = [];
    for (let i = 0; i < 40; i++) {
      const phi1 = Math.acos(2 * Math.random() - 1);
      const theta1 = Math.random() * Math.PI * 2;
      const phi2 = Math.acos(2 * Math.random() - 1);
      const theta2 = Math.random() * Math.PI * 2;
      const r = 2.08;
      for (let t = 0; t <= 20; t++) {
        const f = t / 20;
        const p = 1 + 0.25 * Math.sin(f * Math.PI);
        const ph = phi1 + (phi2 - phi1) * f;
        const th = theta1 + (theta2 - theta1) * f;
        lines.push(p * r * Math.sin(ph) * Math.cos(th), p * r * Math.sin(ph) * Math.sin(th), p * r * Math.cos(ph));
      }
    }
    return new Float32Array(lines);
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.06;
      ref.current.rotation.x = 0.25 + Math.sin(clock.getElapsedTime() * 0.02) * 0.05;
    }
  });

  return (
    <line ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={arcs.length / 3} array={arcs} itemSize={3} />
      </bufferGeometry>
      <lineBasicMaterial color="#ff9b7a" transparent opacity={0.25} />
    </line>
  );
}

function GlobeParticles() {
  const ref = useRef();
  const count = 220;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 2.3 + Math.random() * 1;
      p[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      p[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      p[i * 3 + 2] = r * Math.cos(phi);
    }
    return p;
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.04;
      ref.current.rotation.x = 0.25;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.03} color="#ffb59e" transparent opacity={0.55} sizeAttenuation />
    </points>
  );
}

export function IntegrationsGlobe() {
  return (
    <div style={{ width: '100%', height: '420px', position: 'relative' }}>
      <Canvas
        camera={{ position: [0, 0.3, 5.5], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <ambientLight intensity={0.2} />
        <pointLight position={[5, 3, 5]} intensity={0.6} color="#ff9b7a" distance={18} decay={2} />
        <pointLight position={[-3, -2, 4]} intensity={0.3} color="#ffb59e" distance={15} decay={2} />
        <pointLight position={[0, 0, 6]} intensity={0.15} color="#ff6b4a" distance={10} decay={2} />
        <Suspense fallback={null}>
          <GlobeWireframe />
          <GlobeNodes />
          <ConnectionArcs />
          <GlobeParticles />
        </Suspense>
      </Canvas>
    </div>
  );
}

/* ═══════════ PROCESS PIPELINE — Deep 3D Flow ═══════════ */

function ProcessHub({ position }) {
  const ref = useRef();
  const ringRef = useRef();
  const ring2Ref = useRef();
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref.current) {
      ref.current.rotation.x = t * 0.2;
      ref.current.rotation.z = t * 0.15;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.4;
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.x = t * 0.3;
      ring2Ref.current.rotation.z = -t * 0.2;
    }
  });
  return (
    <group position={position}>
      {/* Outer glow */}
      <Sphere args={[0.7, 20, 20]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={0.25} transparent opacity={0.06} />
      </Sphere>
      {/* Wireframe icosahedron */}
      <group ref={ref}>
        <Icosahedron args={[0.5, 1]}>
          <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.25} />
        </Icosahedron>
      </group>
      {/* Inner bright core */}
      <Sphere args={[0.15, 16, 16]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={2.5} transparent opacity={0.7} />
      </Sphere>
      {/* Orbiting rings — two axes for clear 3D */}
      <group ref={ringRef}>
        <Torus args={[0.6, 0.01, 6, 40]} rotation={[Math.PI / 2.5, 0, 0]}>
          <meshBasicMaterial color="#ff9b7a" transparent opacity={0.3} />
        </Torus>
      </group>
      <group ref={ring2Ref}>
        <Torus args={[0.55, 0.008, 6, 36]} rotation={[0.8, 1.2, 0]}>
          <meshBasicMaterial color="#ffb59e" transparent opacity={0.15} />
        </Torus>
      </group>
    </group>
  );
}

function FlowStream({ from, to }) {
  const ref = useRef();
  const particleCount = 30;

  const positions = useMemo(() => {
    const p = new Float32Array(particleCount * 3);
    const start = new THREE.Vector3(...from);
    const end = new THREE.Vector3(...to);
    for (let i = 0; i < particleCount; i++) {
      const t = i / particleCount;
      const pos = start.clone().lerp(end, t);
      pos.y += Math.sin(t * Math.PI) * 0.4;
      p[i * 3] = pos.x;
      p[i * 3 + 1] = pos.y;
      p[i * 3 + 2] = pos.z;
    }
    return p;
  }, [from, to]);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    const posArr = ref.current.geometry.attributes.position.array;
    const start = new THREE.Vector3(...from);
    const end = new THREE.Vector3(...to);
    for (let i = 0; i < particleCount; i++) {
      const phase = ((i / particleCount) + t * 0.5) % 1;
      const pos = start.clone().lerp(end, phase);
      pos.y += Math.sin(phase * Math.PI) * 0.45;
      pos.z += Math.sin(phase * Math.PI * 2) * 0.15; // Z-depth wave for 3D
      posArr[i * 3] = pos.x;
      posArr[i * 3 + 1] = pos.y;
      posArr[i * 3 + 2] = pos.z;
    }
    ref.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={particleCount} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.06} color="#ff9b7a" transparent opacity={0.85} sizeAttenuation depthWrite={false} />
    </points>
  );
}

function FlowConnector({ from, to }) {
  const points = useMemo(() => {
    const segments = 24;
    const pts = [];
    const start = new THREE.Vector3(...from);
    const end = new THREE.Vector3(...to);
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const pos = start.clone().lerp(end, t);
      pos.y += Math.sin(t * Math.PI) * 0.3;
      pts.push(pos);
    }
    return pts;
  }, [from, to]);
  const geo = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points]);
  return (
    <line geometry={geo}>
      <lineBasicMaterial color="#ff9b7a" transparent opacity={0.3} />
    </line>
  );
}

function ProcessAmbient() {
  const ref = useRef();
  const count = 80;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      p[i * 3] = (Math.random() - 0.5) * 12;
      p[i * 3 + 1] = (Math.random() - 0.5) * 4;
      p[i * 3 + 2] = (Math.random() - 0.5) * 4;
    }
    return p;
  }, []);
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.015;
    }
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.03} color="#ff9b7a" transparent opacity={0.35} sizeAttenuation />
    </points>
  );
}

export function ProcessScene() {
  const nodes = [[-3.5, 0, 0], [-1.2, 0.2, 0.5], [1.2, -0.1, -0.3], [3.5, 0.15, 0.2]];
  return (
    <div style={{ width: '100%', height: '260px' }}>
      <Canvas
        camera={{ position: [0, 1.2, 7], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[0, 4, 5]} intensity={0.7} color="#ff9b7a" distance={18} decay={2} />
        <pointLight position={[-5, -1, 4]} intensity={0.25} color="#ffb59e" distance={12} decay={2} />
        <pointLight position={[5, -1, 4]} intensity={0.25} color="#ffb59e" distance={12} decay={2} />
        <Suspense fallback={null}>
          {nodes.map((pos, i) => (
            <Float key={i} speed={0.8 + i * 0.15} floatIntensity={0.2}>
              <ProcessHub position={pos} />
            </Float>
          ))}
          {nodes.slice(0, -1).map((from, i) => (
            <React.Fragment key={`conn-${i}`}>
              <FlowConnector from={from} to={nodes[i + 1]} />
              <FlowStream from={from} to={nodes[i + 1]} />
            </React.Fragment>
          ))}
          <ProcessAmbient />
        </Suspense>
      </Canvas>
    </div>
  );
}

/* ═══════════ FLOATING ACCENT SHAPES ═══════════ */
export function AccentShapes() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none' }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }} dpr={[1, 1]} gl={{ antialias: false, alpha: true }}>
        <Suspense fallback={null}>
          <Float speed={0.4} rotationIntensity={0.5} floatIntensity={0.6}>
            <Torus args={[1, 0.04, 8, 30]} position={[4, 2, -2]} rotation={[1, 0, 0.5]}>
              <meshBasicMaterial color="#ff9b7a" transparent opacity={0.08} />
            </Torus>
          </Float>
          <Float speed={0.3} rotationIntensity={0.3} floatIntensity={0.4}>
            <Box args={[0.4, 0.4, 0.4]} position={[-4, -1, -1]} rotation={[0.7, 0.3, 0]}>
              <meshBasicMaterial color="#ff9b7a" transparent opacity={0.06} wireframe />
            </Box>
          </Float>
        </Suspense>
      </Canvas>
    </div>
  );
}
