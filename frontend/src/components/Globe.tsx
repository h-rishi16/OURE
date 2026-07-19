'use client';

import React, { useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Stars, useTexture } from '@react-three/drei';
import * as THREE from 'three';
import * as satellite from 'satellite.js';

import { Line } from '@react-three/drei';
import countries from '../countries.json';
import { getCountryBorders } from '../utils/geo';

const earthRadius = 6371;
const initialTime = Date.now();
let simElapsedTime = 0; // Continuously accumulated time so changing speeds doesn't jump
let manualTimeOffset = 0; // Time Scrubber offset

function PhysicsManager({ autoRotate, setAutoRotate }: { autoRotate: boolean, setAutoRotate: (v: boolean) => void }) {
  useFrame((state, delta) => {
    const distance = state.camera.position.length();

    // Normal cinematic speed
    let currentScale = 30;
    let shouldAutoRotate = true;

    // When zoomed in closer than 18,000, drop to 1x real-time (effectively frozen)
    // and stop the camera panning so it's easy to click satellites.
    if (distance < 18000) {
      currentScale = 1;
      shouldAutoRotate = false;
    }

    simElapsedTime += delta * 1000 * currentScale;

    if (shouldAutoRotate !== autoRotate) {
      // Defer state update to avoid React warnings during render phase
      setTimeout(() => setAutoRotate(shouldAutoRotate), 0);
    }
  });

  return null;
}

function Earth() {
  const earthRef = useRef<THREE.Group>(null);

  // Memoize the expensive GeoJSON conversion
  const borders = useMemo(() => {
    return getCountryBorders(countries, earthRadius);
  }, []);

  useFrame(() => {
    if (earthRef.current) {
      const simDate = new Date(initialTime + simElapsedTime + manualTimeOffset);
      const gmst = satellite.gstime(simDate);
      // Satellite.js propagates in ECI coordinates where the Prime Meridian is at +X at GMST=0.
      // Our GeoJSON is now correctly mapped to ECEF, so we just rotate by GMST.
      earthRef.current.rotation.y = gmst;
    }
  });

  return (
    <group ref={earthRef}>
      {/* Invisible sphere to occlude satellites and borders on the far side */}
      <mesh>
        <sphereGeometry args={[earthRadius * 0.99, 64, 64]} />
        <meshBasicMaterial color="#0a0a0a" depthWrite={true} />
      </mesh>

      {/* Country Borders (True Wireframe) */}
      <group>
        {borders.map((points, idx) => (
          <Line
            key={idx}
            points={points}
            color="#a3a3a3"
            lineWidth={0.8}
            transparent
            opacity={0.9}
          />
        ))}
      </group>

      {/* Lat/Lon Grid (Cinematic Wireframe) */}
      <mesh>
        {/* 36 segments for longitude, 18 for latitude gives a clean coordinate grid */}
        <sphereGeometry args={[earthRadius * 1.001, 36, 18]} />
        <meshBasicMaterial
          color="#525252"
          wireframe={true}
          transparent={true}
          opacity={0.4}
          blending={THREE.AdditiveBlending}
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
  onSelectSat,
  focusSatId,
  secondarySatId,
  controlsRef,
  timeOffsetMinutes = 0
}: {
  tleData: string[],
  filter: string,
  onSelectSat: (sat: SatelliteData) => void,
  focusSatId?: string | null,
  secondarySatId?: string | null,
  controlsRef?: React.MutableRefObject<any>,
  timeOffsetMinutes?: number
}) {
  const meshRef = useRef<THREE.Points>(null);
  const ellipsoidRef = useRef<THREE.Mesh>(null);

  const satellites = useMemo(() => {
    const sats: SatelliteData[] = [];
    const getCategory = (name: string) => {
      const n = name.toUpperCase();
      if (n.includes("ISS") || n.includes("ZARYA") || n.includes("TIANGONG") || n.includes("CSS")) return "STATION";
      if (n.includes("STARLINK")) return "STARLINK";
      if (n.includes("ONEWEB") || n.includes("IRIDIUM") || n.includes("GLOBALSTAR") || n.includes("INTELSAT") || n.includes("SES") || n.includes("EUTELSAT") || n.includes("TDRS") || n.includes("O3B") || n.includes("VIASAT") || n.includes("SIRIUS")) return "COMM";
      if (n.includes("NAVSTAR") || n.includes("GLONASS") || n.includes("GALILEO") || n.includes("BEIDOU") || n.includes("GPS") || n.includes("QZS")) return "NAV";
      if (n.includes("NOAA") || n.includes("GOES") || n.includes("METEOR") || n.includes("TERRA") || n.includes("AQUA") || n.includes("HUBBLE") || n.includes("JWST") || n.includes("SENTINEL") || n.includes("LANDSAT") || n.includes("CHANDRA") || n.includes("SUOMI")) return "SCIENCE";
      if (n.includes("USA") || n.includes("COSMOS") || n.includes("KOSMOS") || n.includes("YAOGAN") || n.includes("NOSS") || n.includes("DSP") || n.includes("SBIRS") || n.includes("WGS")) return "MILITARY";
      if (n.includes(" DEB") || n.includes(" R/B") || n.includes("ROCKET") || n.includes("AKM") || n.includes("PKM") || n.includes("BREEZE") || n.includes("FREGAT") || n.includes("DEBRIS") || n.includes("CZ-")) return "DEBRIS";
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
            // Portfolio theme: Monochrome, Silver, Black, White
            let r = 0.25, g = 0.25, b = 0.25; // Default OTHER (Dark Gray)
            if (category === "STATION") { r = 1.0; g = 1.0; b = 1.0; }    // Pure White
            if (category === "STARLINK") { r = 0.85; g = 0.85; b = 0.85; } // Bright Silver
            if (category === "COMM") { r = 0.7; g = 0.7; b = 0.7; }       // Light Gray
            if (category === "NAV") { r = 0.6; g = 0.6; b = 0.6; }        // Medium-Light
            if (category === "SCIENCE") { r = 0.5; g = 0.5; b = 0.5; }    // Medium Gray
            if (category === "MILITARY") { r = 0.4; g = 0.4; b = 0.4; }   // Medium-Dark
            if (category === "DEBRIS") { r = 0.15; g = 0.15; b = 0.15; }  // Very Dark

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

  const isZooming = useRef(false);
  const zoomTimeout = useRef<any>(null);
  const isZoomingOut = useRef(false);
  const zoomOutTimeout = useRef<any>(null);
  const prevFocusRef = useRef<string | null | undefined>(null);

  React.useEffect(() => {
    isZooming.current = !!focusSatId;
    if (prevFocusRef.current && !focusSatId) {
      isZoomingOut.current = true;
      if (zoomOutTimeout.current) clearTimeout(zoomOutTimeout.current);
      zoomOutTimeout.current = setTimeout(() => {
        isZoomingOut.current = false;
      }, 1500);
    }
    prevFocusRef.current = focusSatId;

    if (zoomTimeout.current) clearTimeout(zoomTimeout.current);
    if (focusSatId) {
      zoomTimeout.current = setTimeout(() => {
        isZooming.current = false;
      }, 1500);
    }

    if (!meshRef.current) return;
    const colorAttr = meshRef.current.geometry.attributes.color;
    const colArray = colorAttr.array as Float32Array;

    // Reset all to original colors
    satellites.forEach((sat, i) => {
      colArray[i * 3] = sat.color[0];
      colArray[i * 3 + 1] = sat.color[1];
      colArray[i * 3 + 2] = sat.color[2];
    });

    if (focusSatId) {
      const idx = satellites.findIndex(s => s.id === focusSatId);
      if (idx !== -1) {
        // Blazing Neon Red Highlight for max contrast
        colArray[idx * 3] = 1.0;     // Pure Red
        colArray[idx * 3 + 1] = 0.05; // Tiny bit of green for warmth
        colArray[idx * 3 + 2] = 0.05; // Tiny bit of blue
      }
    }

    if (secondarySatId) {
      const idx2 = satellites.findIndex(s => s.id === secondarySatId);
      if (idx2 !== -1) {
        // Neon Orange/Yellow Highlight for secondary
        colArray[idx2 * 3] = 1.0;
        colArray[idx2 * 3 + 1] = 0.7;
        colArray[idx2 * 3 + 2] = 0.0;
      }
    }

    colorAttr.needsUpdate = true;
  }, [focusSatId, secondarySatId, satellites]);

  const glowTexture = useMemo(() => {
    if (typeof document === 'undefined') return null;
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
    gradient.addColorStop(0.4, 'rgba(255, 255, 255, 1)'); // Solid bright core
    gradient.addColorStop(0.8, 'rgba(255, 255, 255, 0.8)'); // Strong glow
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 64, 64);

    return new THREE.CanvasTexture(canvas);
  }, []);

  const UPDATE_CHUNKS = 5;
  const chunkRef = useRef(0);

  useFrame((state) => {
    if (!meshRef.current) return;

    const posAttr = meshRef.current.geometry.attributes.position;
    const posArray = posAttr.array as Float32Array;

    const simDate = new Date(initialTime + simElapsedTime + manualTimeOffset);

    const chunkSize = Math.ceil(satellites.length / UPDATE_CHUNKS);
    const startIdx = chunkRef.current * chunkSize;
    const endIdx = Math.min(startIdx + chunkSize, satellites.length);

    for (let i = startIdx; i < endIdx; i++) {
      const sat = satellites[i];

      if (filter !== 'ALL' && sat.category !== filter) {
        posArray[i * 3] = 9999999;
        posArray[i * 3 + 1] = 9999999;
        posArray[i * 3 + 2] = 9999999;
        continue;
      }

      const pv = satellite.propagate(sat.satrec, simDate);
      if (pv.position && typeof pv.position !== 'boolean') {
        const p = pv.position as satellite.EciVec3<number>;

        // The GEO belt is at ~42,164 km.
        // We clip anything beyond 43,000 km so there are no stray satellites beyond the equator belt.
        const distSq = p.x * p.x + p.y * p.y + p.z * p.z;
        if (distSq > 43000 * 43000) {
          posArray[i * 3] = 9999999;
          posArray[i * 3 + 1] = 9999999;
          posArray[i * 3 + 2] = 9999999;
          continue;
        }

        posArray[i * 3] = p.x;
        posArray[i * 3 + 1] = p.z;
        posArray[i * 3 + 2] = -p.y;

      } else {
        posArray[i * 3] = 9999999;
        posArray[i * 3 + 1] = 9999999;
        posArray[i * 3 + 2] = 9999999;
      }
    }
    posAttr.needsUpdate = true;
    chunkRef.current = (chunkRef.current + 1) % UPDATE_CHUNKS;

    if (focusSatId && controlsRef?.current) {
      const targetSat = satellites.find(s => s.id === focusSatId);
      if (targetSat) {
        const pv = satellite.propagate(targetSat.satrec, simDate);
        if (pv.position && typeof pv.position !== 'boolean') {
          const p = pv.position as satellite.EciVec3<number>;
          const targetVec = new THREE.Vector3(p.x, p.z, -p.y);

          controlsRef.current.target.lerp(targetVec, 0.08);

          if (isZooming.current) {
            // Place the camera 50% further out from the Earth's center than the satellite itself.
            // Derive this destination from the ALREADY-SMOOTHED target vector, not the raw telemetry,
            // to completely eliminate high-frequency micro-stuttering!
            const desiredPos = controlsRef.current.target.clone().multiplyScalar(1.5);
            state.camera.position.lerp(desiredPos, 0.03);
            if (state.camera.position.distanceTo(desiredPos) < 2000) {
              isZooming.current = false;
            }
          }

          controlsRef.current.update();
        }
      }

      // Render Covariance Ellipsoid for Secondary Target
      if (secondarySatId && ellipsoidRef.current) {
        const secSat = satellites.find(s => s.id === secondarySatId);
        if (secSat) {
          const pv = satellite.propagate(secSat.satrec, simDate);
          if (pv.position && pv.velocity && typeof pv.position !== 'boolean' && typeof pv.velocity !== 'boolean') {
            const p = pv.position as satellite.EciVec3<number>;
            const v = pv.velocity as satellite.EciVec3<number>;
            ellipsoidRef.current.position.set(p.x, p.z, -p.y);

            // Orient the ellipsoid along the velocity vector
            const velVec = new THREE.Vector3(v.x, v.z, -v.y).normalize();
            const up = new THREE.Vector3(0, 1, 0);
            const quaternion = new THREE.Quaternion().setFromUnitVectors(up, velVec);
            ellipsoidRef.current.quaternion.copy(quaternion);

            ellipsoidRef.current.visible = true;
          }
        }
      } else if (ellipsoidRef.current) {
        ellipsoidRef.current.visible = false;
      }

    } else if (!focusSatId && controlsRef?.current) {
      // Smoothly return target to the center of the Earth when deselecting
      const defaultTarget = new THREE.Vector3(0, 0, 0);
      if (controlsRef.current.target && typeof controlsRef.current.target.distanceToSquared === 'function') {
        if (controlsRef.current.target.distanceToSquared(defaultTarget) > 10000) {
          controlsRef.current.target.lerp(defaultTarget, 0.03);
        }
      }

      // Perform a graceful, one-shot cinematic pull-back when deselecting
      if (isZoomingOut.current) {
        const homePos = new THREE.Vector3(0, 5000, 25000);
        state.camera.position.lerp(homePos, 0.03);
        if (state.camera.position.distanceTo(homePos) < 2000) {
          isZoomingOut.current = false;
        }
      }

      // Gentle spherical boundary so you never clip through the Earth manually
      if (state.camera.position.length() < 6400) {
         state.camera.position.setLength(6400);
      }

      controlsRef.current.update();
    }
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
    <>
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
          count={positions.length / 3}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={120}
        vertexColors
        transparent={true}
        opacity={0.8}
        sizeAttenuation={true}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
    <mesh ref={ellipsoidRef} visible={false} scale={[0.5, 3.0, 0.5]}>
      <sphereGeometry args={[80, 32, 32]} />
      <meshBasicMaterial color="#ff0000" transparent opacity={0.6} blending={THREE.AdditiveBlending} depthWrite={false} />
    </mesh>
      <Trajectory focusSatId={focusSatId} satellites={satellites} color="#ff0a2a" />
      <Trajectory focusSatId={secondarySatId} satellites={satellites} color="#ffb703" />
    </>
  );
}

function Trajectory({ focusSatId, satellites, color = "#ff0a2a" }: { focusSatId?: string | null, satellites: SatelliteData[], color?: string }) {
  const points = useMemo(() => {
    if (!focusSatId) return [];
    const sat = satellites.find(s => s.id === focusSatId);
    if (!sat) return [];

    const pts: THREE.Vector3[] = [];
    const baseTime = initialTime + simElapsedTime + manualTimeOffset;

    // Calculate orbital flight path for the next 100 minutes (approx 1 full LEO orbit)
    for (let i = 0; i <= 100; i++) {
      const t = new Date(baseTime + i * 60000); // 1 minute steps
      const pv = satellite.propagate(sat.satrec, t);
      if (pv.position && typeof pv.position !== 'boolean') {
        const p = pv.position as satellite.EciVec3<number>;
        pts.push(new THREE.Vector3(p.x, p.z, -p.y));
      }
    }
    return pts;
  }, [focusSatId, satellites]);

  if (points.length < 2) return null;

  return (
    <Line
      points={points}
      color={color}
      lineWidth={2.5}
      transparent
      opacity={0.7}
    />
  );
}



function DynamicRaycaster() {
  const { camera, raycaster } = useThree();
  useFrame(() => {
    // Dynamically scale the raycaster threshold based on camera distance!
    // At LEO (10,000 units away), threshold is ~25 (super precise).
    // At GEO (100,000 units away), threshold is ~250 (large enough to click from far).
    const dist = camera.position.length();
    const dynamicThreshold = Math.max(15, dist * 0.0025);
    (raycaster as any).params.Points.threshold = dynamicThreshold;
  });
  return null;
}

export default function Globe({
  tleData,
  filter,
  onSelectSat,
  focusSatId,
  secondarySatId,
  timeOffsetMinutes = 0
}: {
  tleData: string[],
  filter: string,
  onSelectSat: (sat: SatelliteData) => void,
  focusSatId?: string | null,
  secondarySatId?: string | null,
  timeOffsetMinutes?: number
}) {
  manualTimeOffset = timeOffsetMinutes * 60000;
  const [autoRotate, setAutoRotate] = useState(true);
  const controlsRef = useRef<any>(null);

  return (
    <div className="w-full h-full relative cursor-crosshair">
      <Canvas
        camera={{ position: [0, 5000, 25000], fov: 45, near: 1, far: 400000 }}
        gl={{ antialias: true, alpha: true, logarithmicDepthBuffer: true }}
      >
        <DynamicRaycaster />
        <PhysicsManager autoRotate={autoRotate} setAutoRotate={setAutoRotate} />

        <ambientLight intensity={1.5} color={0x404040} />
        <directionalLight position={[50000, 20000, 30000]} intensity={2.5} color={0xffffff} />

        <Stars radius={10000} depth={200000} count={20000} factor={3} saturation={0} />

        <Earth />

        <Satellites tleData={tleData} filter={filter} onSelectSat={onSelectSat} focusSatId={focusSatId} secondarySatId={secondarySatId} controlsRef={controlsRef} timeOffsetMinutes={timeOffsetMinutes} />

        <OrbitControls
          ref={controlsRef}
          enableDamping
          dampingFactor={0.05}
          minDistance={focusSatId ? 100 : 7000}
          maxDistance={120000}
          enablePan={true}
          autoRotate={focusSatId ? false : autoRotate}
          autoRotateSpeed={0.15}
        />
      </Canvas>
    </div>
  );
}
