import React, { useRef, useMemo, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial, Sphere, Box, Torus, Icosahedron, Octahedron } from '@react-three/drei';
import * as THREE from 'three';

/* ═══════════ HERO — Neural Network Constellation ═══════════ */
const NODE_COUNT = 80;
const EDGE_COUNT = 100;

function NetworkNodes() {
  const meshRef = useRef();
  const positions = useMemo(() => {
    const pos = new Float32Array(NODE_COUNT * 3);
    for (let i = 0; i < NODE_COUNT; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 10;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 7;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 5;
    }
    return pos;
  }, []);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime() * 0.12;
    const posArr = meshRef.current.geometry.attributes.position.array;
    for (let i = 0; i < NODE_COUNT; i++) {
      posArr[i * 3] += Math.sin(t + i * 0.4) * 0.0008;
      posArr[i * 3 + 1] += Math.cos(t + i * 0.25) * 0.0008;
    }
    meshRef.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={NODE_COUNT} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.05} color="#ff9b7a" transparent opacity={0.7} sizeAttenuation />
    </points>
  );
}

function NetworkEdges() {
  const linesRef = useRef();
  const positions = useMemo(() => {
    const pos = [];
    for (let i = 0; i < EDGE_COUNT; i++) {
      const x1 = (Math.random() - 0.5) * 10, y1 = (Math.random() - 0.5) * 7, z1 = (Math.random() - 0.5) * 5;
      const x2 = x1 + (Math.random() - 0.5) * 2.5, y2 = y1 + (Math.random() - 0.5) * 1.8, z2 = z1 + (Math.random() - 0.5) * 1.5;
      pos.push(x1, y1, z1, x2, y2, z2);
    }
    return new Float32Array(pos);
  }, []);

  useFrame(({ clock }) => {
    if (linesRef.current) {
      linesRef.current.rotation.y = clock.getElapsedTime() * 0.015;
      linesRef.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.008) * 0.03;
    }
  });

  return (
    <lineSegments ref={linesRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={EDGE_COUNT * 2} array={positions} itemSize={3} />
      </bufferGeometry>
      <lineBasicMaterial color="#ff9b7a" transparent opacity={0.06} />
    </lineSegments>
  );
}

function FloatingCore() {
  const ref = useRef();
  const innerRef = useRef();
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref.current) {
      ref.current.rotation.x = t * 0.08;
      ref.current.rotation.y = t * 0.12;
    }
    if (innerRef.current) {
      innerRef.current.rotation.x = t * -0.05;
      innerRef.current.rotation.z = t * 0.07;
    }
  });
  return (
    <group position={[1.5, 0, 0]}>
      <group ref={ref}>
        <Icosahedron args={[1.4, 1]}>
          <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.1} />
        </Icosahedron>
      </group>
      <group ref={innerRef}>
        <Icosahedron args={[1.0, 0]}>
          <MeshDistortMaterial color="#ff9b7a" transparent opacity={0.04} distort={0.25} speed={1.5} />
        </Icosahedron>
      </group>
      <Sphere args={[0.2, 16, 16]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={0.8} transparent opacity={0.15} />
      </Sphere>
    </group>
  );
}

function DataStreams() {
  const ref = useRef();
  const count = 300;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 10;
      const radius = 1.5 + Math.random() * 4;
      p[i * 3] = Math.cos(angle) * radius;
      p[i * 3 + 1] = (Math.random() - 0.5) * 7;
      p[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return p;
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.03;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.015} color="#ffb59e" transparent opacity={0.3} sizeAttenuation />
    </points>
  );
}

function AccentGeometries() {
  return (
    <>
      <Float speed={0.5} rotationIntensity={0.2} floatIntensity={0.3}>
        <Sphere args={[0.12, 16, 16]} position={[4, 2.5, -1.5]}>
          <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={0.6} transparent opacity={0.5} />
        </Sphere>
      </Float>
      <Float speed={0.8} rotationIntensity={0.3} floatIntensity={0.4}>
        <Box args={[0.18, 0.18, 0.18]} position={[-4, -2, 0.5]} rotation={[0.5, 0.5, 0]}>
          <meshBasicMaterial color="#ff9b7a" transparent opacity={0.08} wireframe />
        </Box>
      </Float>
      <Float speed={0.6} rotationIntensity={0.15} floatIntensity={0.2}>
        <Torus args={[0.25, 0.06, 8, 24]} position={[4.5, -2.5, -1]} rotation={[1, 0.5, 0]}>
          <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={0.2} transparent opacity={0.2} />
        </Torus>
      </Float>
      <Float speed={0.4} rotationIntensity={0.1} floatIntensity={0.15}>
        <Icosahedron args={[0.1, 0]} position={[-3, 2, -1]}>
          <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.12} />
        </Icosahedron>
      </Float>
      <Float speed={0.7} rotationIntensity={0.2} floatIntensity={0.25}>
        <Sphere args={[0.06, 8, 8]} position={[2, -3, 0]}>
          <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={1} transparent opacity={0.4} />
        </Sphere>
      </Float>
    </>
  );
}

export function HeroScene() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      <Canvas
        camera={{ position: [0, 0, 6], fov: 60 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <ambientLight intensity={0.2} />
        <pointLight position={[5, 5, 5]} intensity={0.4} color="#ff9b7a" distance={20} decay={2} />
        <pointLight position={[-4, -3, 3]} intensity={0.15} color="#ff9b7a" distance={15} decay={2} />
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

/* ═══════════ INTEGRATIONS GLOBE — Premium Wireframe ═══════════ */
function GlobeWireframe() {
  const ref = useRef();
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.05;
      ref.current.rotation.x = 0.2;
    }
  });
  return (
    <group ref={ref}>
      <Sphere args={[2, 32, 32]}>
        <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.07} />
      </Sphere>
      <Sphere args={[2.1, 20, 20]}>
        <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.03} />
      </Sphere>
      {/* Equatorial ring */}
      <Torus args={[2.06, 0.012, 8, 64]} rotation={[Math.PI / 2, 0, 0]}>
        <meshBasicMaterial color="#ff9b7a" transparent opacity={0.18} />
      </Torus>
      {/* Polar ring */}
      <Torus args={[2.06, 0.008, 8, 64]} rotation={[0, 0, 0]}>
        <meshBasicMaterial color="#ff9b7a" transparent opacity={0.08} />
      </Torus>
      {/* Angled ring */}
      <Torus args={[2.06, 0.006, 8, 64]} rotation={[Math.PI / 3, Math.PI / 4, 0]}>
        <meshBasicMaterial color="#ff9b7a" transparent opacity={0.06} />
      </Torus>
      {/* Central glow */}
      <Sphere args={[0.15, 12, 12]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={1.2} transparent opacity={0.2} />
      </Sphere>
    </group>
  );
}

function GlobeNodes() {
  const ref = useRef();
  const count = 70;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 2.06;
      p[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      p[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      p[i * 3 + 2] = r * Math.cos(phi);
    }
    return p;
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.05;
      ref.current.rotation.x = 0.2;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.08} color="#ff9b7a" transparent opacity={0.9} sizeAttenuation />
    </points>
  );
}

function ConnectionArcs() {
  const ref = useRef();
  const arcs = useMemo(() => {
    const lines = [];
    for (let i = 0; i < 22; i++) {
      const phi1 = Math.acos(2 * Math.random() - 1);
      const theta1 = Math.random() * Math.PI * 2;
      const phi2 = Math.acos(2 * Math.random() - 1);
      const theta2 = Math.random() * Math.PI * 2;
      const r = 2.06;
      for (let t = 0; t <= 16; t++) {
        const f = t / 16;
        const p = 1 + 0.2 * Math.sin(f * Math.PI);
        const ph = phi1 + (phi2 - phi1) * f;
        const th = theta1 + (theta2 - theta1) * f;
        lines.push(p * r * Math.sin(ph) * Math.cos(th), p * r * Math.sin(ph) * Math.sin(th), p * r * Math.cos(ph));
      }
    }
    return new Float32Array(lines);
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.05;
      ref.current.rotation.x = 0.2;
    }
  });

  return (
    <line ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={arcs.length / 3} array={arcs} itemSize={3} />
      </bufferGeometry>
      <lineBasicMaterial color="#ff9b7a" transparent opacity={0.15} />
    </line>
  );
}

/* Floating data particles around globe */
function GlobeParticles() {
  const ref = useRef();
  const count = 120;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 2.2 + Math.random() * 0.8;
      p[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      p[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      p[i * 3 + 2] = r * Math.cos(phi);
    }
    return p;
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.03;
      ref.current.rotation.x = 0.2;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.02} color="#ffb59e" transparent opacity={0.4} sizeAttenuation />
    </points>
  );
}

export function IntegrationsGlobe() {
  return (
    <div style={{ width: '100%', height: '380px', position: 'relative' }}>
      <Canvas
        camera={{ position: [0, 0, 5.5], fov: 50 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <ambientLight intensity={0.15} />
        <pointLight position={[5, 3, 5]} intensity={0.35} color="#ff9b7a" distance={15} decay={2} />
        <pointLight position={[-3, -2, 4]} intensity={0.15} color="#ffb59e" distance={12} decay={2} />
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

/* ═══════════ PROCESS PIPELINE — Premium Flow Visualization ═══════════ */

/* Central process hub */
function ProcessHub({ position }) {
  const ref = useRef();
  const ringRef = useRef();
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref.current) {
      ref.current.rotation.x = t * 0.15;
      ref.current.rotation.z = t * 0.1;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.3;
    }
  });
  return (
    <group position={position}>
      {/* Outer glow sphere */}
      <Sphere args={[0.65, 20, 20]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={0.15} transparent opacity={0.04} />
      </Sphere>
      {/* Wireframe icosahedron */}
      <group ref={ref}>
        <Icosahedron args={[0.45, 1]}>
          <meshBasicMaterial color="#ff9b7a" wireframe transparent opacity={0.15} />
        </Icosahedron>
      </group>
      {/* Inner solid core */}
      <Sphere args={[0.12, 12, 12]}>
        <meshStandardMaterial color="#ff9b7a" emissive="#ff9b7a" emissiveIntensity={1.5} transparent opacity={0.6} />
      </Sphere>
      {/* Orbiting ring */}
      <group ref={ringRef}>
        <Torus args={[0.55, 0.008, 6, 40]} rotation={[Math.PI / 2.5, 0, 0]}>
          <meshBasicMaterial color="#ff9b7a" transparent opacity={0.2} />
        </Torus>
      </group>
    </group>
  );
}

/* Data flow particle streams between nodes */
function FlowStream({ from, to }) {
  const ref = useRef();
  const particleCount = 20;

  const positions = useMemo(() => {
    const p = new Float32Array(particleCount * 3);
    const start = new THREE.Vector3(...from);
    const end = new THREE.Vector3(...to);
    for (let i = 0; i < particleCount; i++) {
      const t = i / particleCount;
      const pos = start.clone().lerp(end, t);
      pos.y += Math.sin(t * Math.PI) * 0.3;
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
      const phase = ((i / particleCount) + t * 0.4) % 1;
      const pos = start.clone().lerp(end, phase);
      pos.y += Math.sin(phase * Math.PI) * 0.35;
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
      <pointsMaterial size={0.04} color="#ff9b7a" transparent opacity={0.7} sizeAttenuation />
    </points>
  );
}

/* Connection line with glow */
function FlowConnector({ from, to }) {
  const points = useMemo(() => {
    const segments = 20;
    const pts = [];
    const start = new THREE.Vector3(...from);
    const end = new THREE.Vector3(...to);
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const pos = start.clone().lerp(end, t);
      pos.y += Math.sin(t * Math.PI) * 0.25;
      pts.push(pos);
    }
    return pts;
  }, [from, to]);
  const geo = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points]);
  return (
    <group>
      <line geometry={geo}>
        <lineBasicMaterial color="#ff9b7a" transparent opacity={0.2} />
      </line>
    </group>
  );
}

/* Ambient environment particles */
function ProcessAmbient() {
  const ref = useRef();
  const count = 60;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      p[i * 3] = (Math.random() - 0.5) * 10;
      p[i * 3 + 1] = (Math.random() - 0.5) * 3;
      p[i * 3 + 2] = (Math.random() - 0.5) * 3;
    }
    return p;
  }, []);
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.01;
    }
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.02} color="#ff9b7a" transparent opacity={0.25} sizeAttenuation />
    </points>
  );
}

export function ProcessScene() {
  const nodes = [[-3.5, 0, 0], [-1.2, 0, 0], [1.2, 0, 0], [3.5, 0, 0]];
  return (
    <div style={{ width: '100%', height: '220px' }}>
      <Canvas
        camera={{ position: [0, 0.5, 6], fov: 50 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <ambientLight intensity={0.25} />
        <pointLight position={[0, 3, 4]} intensity={0.5} color="#ff9b7a" distance={15} decay={2} />
        <pointLight position={[-4, -1, 3]} intensity={0.15} color="#ffb59e" distance={10} decay={2} />
        <pointLight position={[4, -1, 3]} intensity={0.15} color="#ffb59e" distance={10} decay={2} />
        <Suspense fallback={null}>
          {nodes.map((pos, i) => (
            <Float key={i} speed={0.8 + i * 0.15} floatIntensity={0.15}>
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

/* ═══════════ FLOATING ACCENT SHAPES (reusable) ═══════════ */
export function AccentShapes() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none' }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }} dpr={[1, 1]} gl={{ antialias: false, alpha: true }}>
        <Suspense fallback={null}>
          <Float speed={0.4} rotationIntensity={0.5} floatIntensity={0.6}>
            <Torus args={[1, 0.04, 8, 30]} position={[4, 2, -2]} rotation={[1, 0, 0.5]}>
              <meshBasicMaterial color="#ff9b7a" transparent opacity={0.06} />
            </Torus>
          </Float>
          <Float speed={0.3} rotationIntensity={0.3} floatIntensity={0.4}>
            <Box args={[0.4, 0.4, 0.4]} position={[-4, -1, -1]} rotation={[0.7, 0.3, 0]}>
              <meshBasicMaterial color="#ff9b7a" transparent opacity={0.04} wireframe />
            </Box>
          </Float>
        </Suspense>
      </Canvas>
    </div>
  );
}
