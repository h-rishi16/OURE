'use client';

import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, useTexture } from '@react-three/drei';
import * as THREE from 'three';
import * as satellite from 'satellite.js';

const earthRadius = 6371;

function Earth() {
  const [colorMap, specularMap, bumpMap, cloudMap] = useTexture([
    'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg',
    'https://unpkg.com/three-globe/example/img/earth-water.png',
    'https://unpkg.com/three-globe/example/img/earth-topology.png',
    'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_clouds_1024.png'
  ]);

  const earthRef = useRef<THREE.Mesh>(null);
  const cloudRef = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (earthRef.current && cloudRef.current) {
      const gmst = satellite.gstime(new Date());
      earthRef.current.rotation.y = gmst;
      cloudRef.current.rotation.y = gmst * 1.05;
    }
  });

  return (
    <group>
      <mesh ref={earthRef}>
        <sphereGeometry args={[earthRadius, 64, 64]} />
        <meshPhongMaterial
          map={colorMap}
          specularMap={specularMap}
          bumpMap={bumpMap}
          bumpScale={15}
          specular={new THREE.Color(0x333333)}
          shininess={15}
        />
      </mesh>
      <mesh ref={cloudRef}>
        <sphereGeometry args={[earthRadius * 1.01, 64, 64]} />
        <meshPhongMaterial
          map={cloudMap}
          transparent
          opacity={0.8}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

export interface SatelliteData {
  name: string;
  id: string;
  category: string;
  satrec: satellite.SatRec;
  color: [number, number, number];
}

function Satellites({
  tleData,
  filter,
  onSelectSat
}: {
  tleData: string[],
  filter: string,
  onSelectSat: (sat: SatelliteData) => void
}) {
  const meshRef = useRef<THREE.Points>(null);

  const satellites = useMemo(() => {
    const sats: SatelliteData[] = [];
    const getCategory = (name: string) => {
      if (name.includes("ISS") || name.includes("ZARYA") || name.includes("CSS") || name.includes("TIANGONG")) return "STATION";
      if (name.includes("STARLINK")) return "STARLINK";
      if (name.includes("ONEWEB")) return "ONEWEB";
      if (name.includes("NOAA") || name.includes("GOES") || name.includes("METEOR") || name.includes("TERRA") || name.includes("AQUA") || name.includes("FLOCK") || name.includes("LANDSAT")) return "WEATHER";
      if (name.includes("NAVSTAR") || name.includes("GLONASS") || name.includes("GALILEO") || name.includes("BEIDOU") || name.includes("GPS") || name.includes("QZS")) return "NAV";
      return "OTHER";
    };

    for (let i = 0; i < tleData.length; i++) {
      if (tleData[i].startsWith('1 ') && i > 0 && i + 1 < tleData.length) {
        const name = tleData[i - 1];
        const tle1 = tleData[i];
        const tle2 = tleData[i + 1];
        const noradId = tle1.substring(2, 7).trim();
        const category = getCategory(name);

        try {
          const satrec = satellite.twoline2satrec(tle1, tle2);
          if (satrec.error === 0) {
            let r = 0.4, g = 0.5, b = 0.7; // Default OTHER
            if (category === "STARLINK") { r = 0.1; g = 0.9; b = 0.3; } // Green
            if (category === "ONEWEB") { r = 0.8; g = 0.2; b = 0.9; }   // Purple
            if (category === "STATION") { r = 1.0; g = 1.0; b = 1.0; }  // White
            if (category === "WEATHER") { r = 0.2; g = 0.8; b = 1.0; }  // Cyan
            if (category === "NAV") { r = 1.0; g = 0.8; b = 0.2; }      // Yellow

            sats.push({ name, id: noradId, category, satrec, color: [r, g, b] });
          }
        } catch {
          // ignore
        }
      }
    }
    return sats;
  }, [tleData]);

  const [positions, colors] = useMemo(() => {
    const pos = new Float32Array(satellites.length * 3);
    const col = new Float32Array(satellites.length * 3);
    satellites.forEach((sat, i) => {
      col[i * 3] = sat.color[0];
      col[i * 3 + 1] = sat.color[1];
      col[i * 3 + 2] = sat.color[2];
    });
    return [pos, col];
  }, [satellites]);

  const UPDATE_CHUNKS = 15;
  const chunkRef = useRef(0);

  useFrame(() => {
    if (!meshRef.current) return;

    const posAttr = meshRef.current.geometry.attributes.position;
    const posArray = posAttr.array as Float32Array;

    const simDate = new Date(); // Could use a time offset here

    const chunkSize = Math.ceil(satellites.length / UPDATE_CHUNKS);
    const startIdx = chunkRef.current * chunkSize;
    const endIdx = Math.min(startIdx + chunkSize, satellites.length);

    for (let i = startIdx; i < endIdx; i++) {
      const sat = satellites[i];

      if (filter !== 'ALL' && sat.category !== filter) {
        posArray[i * 3] = 0;
        posArray[i * 3 + 1] = 0;
        posArray[i * 3 + 2] = 0;
        continue;
      }

      const pv = satellite.propagate(sat.satrec, simDate);
      if (pv.position && typeof pv.position !== 'boolean') {
        const p = pv.position as satellite.EciVec3<number>;
        posArray[i * 3] = p.x;
        posArray[i * 3 + 1] = p.z;
        posArray[i * 3 + 2] = -p.y;
      } else {
        posArray[i * 3] = 0;
        posArray[i * 3 + 1] = 0;
        posArray[i * 3 + 2] = 0;
      }
    }
    posAttr.needsUpdate = true;
    chunkRef.current = (chunkRef.current + 1) % UPDATE_CHUNKS;
  });

  const handlePointerDown = (e: import('@react-three/fiber').ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    if (e.index !== undefined) {
      const sat = satellites[e.index];
      if (filter === 'ALL' || sat.category === filter) {
        onSelectSat(sat);
      }
    }
  };

  return (
    <points ref={meshRef} onPointerDown={handlePointerDown}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={colors.length / 3}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={90}
        vertexColors
        sizeAttenuation
        transparent
        opacity={0.8}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}

export default function Globe({
  tleData,
  filter,
  onSelectSat
}: {
  tleData: string[],
  filter: string,
  onSelectSat: (sat: SatelliteData) => void
}) {
  return (
    <div className="w-full h-full relative cursor-crosshair">
      <Canvas
        camera={{ position: [0, 5000, 25000], fov: 45, near: 1, far: 100000 }}
        gl={{ antialias: true, alpha: true, logarithmicDepthBuffer: true }}
      >
        <ambientLight intensity={1.5} color={0x404040} />
        <directionalLight position={[50000, 20000, 30000]} intensity={2.5} color={0xffffff} />

        <Stars radius={200000} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />

        <Earth />

        <Satellites tleData={tleData} filter={filter} onSelectSat={onSelectSat} />

        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={7000}
          maxDistance={50000}
          enablePan={false}
        />
      </Canvas>
    </div>
  );
}
