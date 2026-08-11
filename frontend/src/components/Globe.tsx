'use client';

import React, { useMemo, useRef, useState, useEffect } from 'react';
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
    // Exception: Do not freeze during the initial 3-second cinematic boot sequence.
    if (distance < 18000 && state.clock.elapsedTime > 3) {
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
      {/* Invisible sphere to occlude satellites and borders on the far side visually AND interactively */}
      <mesh onPointerDown={(e) => e.stopPropagation()}>
        <sphereGeometry args={[earthRadius * 0.99, 64, 64]} />
        <meshBasicMaterial color="#0a0a0a" depthWrite={true} />
      </mesh>

      {/* Country Borders (High Performance LineSegments) */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={borders.length / 3}
            array={borders}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#a3a3a3" transparent opacity={0.4} />
      </lineSegments>

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
  timeOffsetMinutes = 0,
  escapeTrajectory,
  warningLevel
}: {
  tleData: string[],
  filter: string,
  onSelectSat: (sat: SatelliteData) => void,
  focusSatId?: string | null,
  secondarySatId?: string | null,
  controlsRef?: React.MutableRefObject<any>,
  timeOffsetMinutes?: number,
  escapeTrajectory?: number[][] | null,
  warningLevel?: string | null
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
        let name = tleData[i - 1];
        if (name.startsWith('0 ')) name = name.substring(2);
        const tle1 = tleData[i];
        const tle2 = tleData[i + 1];
        const noradId = tle1.substring(2, 7).trim();
        const category = getCategory(name);

        try {
          const satrec = satellite.twoline2satrec(tle1, tle2);
          if (satrec.error === 0) {
            let r = 0.25, g = 0.25, b = 0.25;
            if (category === "STATION") { r = 1.0; g = 1.0; b = 1.0; }
            if (category === "STARLINK") { r = 0.85; g = 0.85; b = 0.85; }
            if (category === "COMM") { r = 0.7; g = 0.7; b = 0.7; }
            if (category === "NAV") { r = 0.6; g = 0.6; b = 0.6; }
            if (category === "SCIENCE") { r = 0.5; g = 0.5; b = 0.5; }
            if (category === "MILITARY") { r = 0.4; g = 0.4; b = 0.4; }
            if (category === "DEBRIS") { r = 0.15; g = 0.15; b = 0.15; }

            sats.push({ name, id: noradId, category, satrec, color: [r, g, b] });
          }
        } catch {
        }
      }
    }

    const starmanSatrec = satellite.twoline2satrec(
      "1 43205U 18017A   23001.00000000  .00000000  00000-0  00000-0 0  9991",
      "2 43205  51.6400  10.0000 0005000   0.0000   0.0000 15.50000000    02"
    );
    sats.push({
      name: "STARMAN (TESLA ROADSTER) 🚗",
      id: "43205",
      category: "STARMAN",
      satrec: starmanSatrec,
      color: [1.0, 0.0, 0.0]
    });

    return sats;
  }, [tleData]);

  const [positions, colors, velocities, updateTimes] = useMemo(() => {
    const pos = new Float32Array(satellites.length * 3);
    const col = new Float32Array(satellites.length * 3);
    const vel = new Float32Array(satellites.length * 3);
    const upT = new Float32Array(satellites.length);
    satellites.forEach((sat, i) => {
      col[i * 3] = sat.color[0];
      col[i * 3 + 1] = sat.color[1];
      col[i * 3 + 2] = sat.color[2];
    });
    return [pos, col, vel, upT];
  }, [satellites]);

  const isZooming = useRef(false);
  const zoomTimeout = useRef<any>(null);
  const isZoomingOut = useRef(true);
  const zoomOutTimeout = useRef<any>(null);
  const prevFocusRef = useRef<string | null | undefined>(null);

  React.useEffect(() => {
    const bootTimer = setTimeout(() => {
      isZoomingOut.current = false;
    }, 2500);
    return () => clearTimeout(bootTimer);
  }, []);

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

    satellites.forEach((sat, i) => {
      colArray[i * 3] = sat.color[0];
      colArray[i * 3 + 1] = sat.color[1];
      colArray[i * 3 + 2] = sat.color[2];
    });

    if (focusSatId) {
      const idx = satellites.findIndex(s => s.id === focusSatId);
      if (idx !== -1) {
        colArray[idx * 3] = 0.0;
        colArray[idx * 3 + 1] = 1.0;
        colArray[idx * 3 + 2] = 1.0;
      }
    }

    if (secondarySatId) {
      const idx2 = satellites.findIndex(s => s.id === secondarySatId);
      if (idx2 !== -1) {
        colArray[idx2 * 3] = 1.0;
        colArray[idx2 * 3 + 1] = 0.7;
        colArray[idx2 * 3 + 2] = 0.0;
      }
    }

    colorAttr.needsUpdate = true;
  }, [focusSatId, secondarySatId, satellites]);

  const UPDATE_CHUNKS = 30;
  const chunkRef = useRef(0);

  useFrame((state) => {
    if (!meshRef.current) return;

    const posAttr = meshRef.current.geometry.attributes.position;
    const posArray = posAttr.array as Float32Array;
    const velAttr = meshRef.current.geometry.attributes.velocity;
    const velArray = velAttr ? velAttr.array as Float32Array : null;
    const timeAttr = meshRef.current.geometry.attributes.updateTime;
    const timeArray = timeAttr ? timeAttr.array as Float32Array : null;

    const simTimeMs = initialTime + simElapsedTime + manualTimeOffset;
    const simDate = new Date(simTimeMs);

    const material = meshRef.current.material as any;
    if (material && material.userData && material.userData.shader) {
      material.userData.shader.uniforms.uSimTime.value = simElapsedTime / 1000.0;
    }

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
      if (pv.position && pv.velocity && typeof pv.position !== 'boolean' && typeof pv.velocity !== 'boolean') {
        const p = pv.position as satellite.EciVec3<number>;
        const v = pv.velocity as satellite.EciVec3<number>;
        const distSq = p.x * p.x + p.y * p.y + p.z * p.z;
        if (distSq > 43000 * 43000 && sat.id !== '43205') {
          posArray[i * 3] = 9999999;
          posArray[i * 3 + 1] = 9999999;
          posArray[i * 3 + 2] = 9999999;
          continue;
        }

        posArray[i * 3] = p.x;
        posArray[i * 3 + 1] = p.z;
        posArray[i * 3 + 2] = -p.y;

        if (velArray && timeArray) {
          velArray[i * 3] = v.x;
          velArray[i * 3 + 1] = v.z;
          velArray[i * 3 + 2] = -v.y;
          timeArray[i] = simElapsedTime / 1000.0;
        }

      } else {
        posArray[i * 3] = 9999999;
        posArray[i * 3 + 1] = 9999999;
        posArray[i * 3 + 2] = 9999999;
      }
    }
    posAttr.needsUpdate = true;
    if (velAttr) velAttr.needsUpdate = true;
    if (timeAttr) timeAttr.needsUpdate = true;
    chunkRef.current = (chunkRef.current + 1) % UPDATE_CHUNKS;

    if (focusSatId && controlsRef?.current) {
      const targetSat = satellites.find(s => s.id === focusSatId);
      if (targetSat || focusSatId === 'JWST-1') {
        let targetVec = new THREE.Vector3();
        let valid = false;

        if (focusSatId === 'JWST-1') {
          targetVec.set(150000, 0, 0);
          valid = true;

        } else if (targetSat) {
          const pv = satellite.propagate(targetSat.satrec, simDate);
          if (pv.position && typeof pv.position !== 'boolean') {
            const p = pv.position as satellite.EciVec3<number>;
            targetVec.set(p.x, p.z, -p.y);
            valid = true;
          }
        }

        if (valid) {
          controlsRef.current.target.lerp(targetVec, 0.08);

          if (isZooming.current) {
            const desiredPos = controlsRef.current.target.clone().multiplyScalar(1.5);
            state.camera.position.lerp(desiredPos, 0.03);
            if (state.camera.position.distanceTo(desiredPos) < 2000) {
              isZooming.current = false;
            }
          }

          controlsRef.current.update();
        }
      }

      if (secondarySatId && ellipsoidRef.current) {
        const secSat = satellites.find(s => s.id === secondarySatId);
        if (secSat) {
          const pv = satellite.propagate(secSat.satrec, simDate);
          if (pv.position && pv.velocity && typeof pv.position !== 'boolean' && typeof pv.velocity !== 'boolean') {
            const p = pv.position as satellite.EciVec3<number>;
            const v = pv.velocity as satellite.EciVec3<number>;
            ellipsoidRef.current.position.set(p.x, p.z, -p.y);

            const velVec = new THREE.Vector3(v.x, v.z, -v.y).normalize();
            const up = new THREE.Vector3(0, 1, 0);
            const quaternion = new THREE.Quaternion().setFromUnitVectors(up, velVec);
            ellipsoidRef.current.quaternion.copy(quaternion);

            ellipsoidRef.current.visible = true;
          } else {
            ellipsoidRef.current.visible = false;
          }
        } else {
          ellipsoidRef.current.visible = false;
        }
      } else if (ellipsoidRef.current) {
        ellipsoidRef.current.visible = false;
      }

    } else if (!focusSatId && controlsRef?.current) {
      const defaultTarget = new THREE.Vector3(0, 0, 0);
      if (controlsRef.current.target && typeof controlsRef.current.target.distanceToSquared === 'function') {
        if (controlsRef.current.target.distanceToSquared(defaultTarget) > 10000) {
          controlsRef.current.target.lerp(defaultTarget, 0.03);
        }
      }

      if (ellipsoidRef.current) {
        ellipsoidRef.current.visible = false;
      }

      if (isZoomingOut.current) {
        const homePos = new THREE.Vector3(0, 5000, 25000);
        state.camera.position.lerp(homePos, 0.015);
        if (state.camera.position.distanceTo(homePos) < 500) {
          isZoomingOut.current = false;
        }
      }

      if (state.camera.position.length() < 6400) {
         state.camera.position.setLength(6400);
      }

      controlsRef.current.update();
    }
  });

  const downState = useRef({ time: 0, x: 0, y: 0, cam: new THREE.Vector3() });

  const handlePointerDown = (e: import('@react-three/fiber').ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    downState.current = {
      time: performance.now(),
      x: e.clientX,
      y: e.clientY,
      cam: e.camera.position.clone()
    };
  };

  const handlePointerUp = (e: import('@react-three/fiber').ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    const timeDelta = performance.now() - downState.current.time;
    const dist = Math.hypot(e.clientX - downState.current.x, e.clientY - downState.current.y);
    const camMoved = e.camera.position.distanceTo(downState.current.cam);

    // Relaxed camera movement threshold (50) so auto-rotation doesn't accidentally cancel clicks
    if (timeDelta > 500 || dist > 15 || camMoved > 50) {
      return;
    }

    if (e.index !== undefined) {
      const sat = satellites[e.index];
      if (filter === 'ALL' || sat.category === filter) {
        onSelectSat(sat);
      }
    }
  };

  return (
    <>
    <points ref={meshRef} onPointerDown={handlePointerDown} onPointerUp={handlePointerUp}>
      <bufferGeometry key={satellites.length}>
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
        <bufferAttribute
          attach="attributes-velocity"
          count={positions.length / 3}
          array={velocities}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-updateTime"
          count={positions.length / 3}
          array={updateTimes}
          itemSize={1}
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
        onBeforeCompile={(shader) => {
          shader.uniforms.uSimTime = { value: 0 };
          shader.vertexShader = `
            uniform float uSimTime;
            attribute vec3 velocity;
            attribute float updateTime;
            ${shader.vertexShader}
          `.replace(
            `#include <begin_vertex>`,
            `
            vec3 transformed = vec3( position );
            float dt = uSimTime - updateTime;
            // Cap delta time to prevent wild extrapolation during initial load or heavy lag
            if (dt > 0.0 && dt < 2.0 && updateTime > 0.0) {
              transformed += velocity * dt;
            }
            `
          );
          (meshRef.current as any).material.userData.shader = shader;
        }}
      />
    </points>
    <group ref={ellipsoidRef} visible={false}>
      <mesh scale={
        warningLevel === 'RED' ? [0.5, 3.0, 0.5] : [0.3, 1.5, 0.3]
      }>
        <sphereGeometry args={[80, 32, 32]} />
        <meshBasicMaterial
          color={warningLevel === 'RED' ? "#ef4444" : "#ffffff"}
          transparent opacity={0.1} blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </mesh>

      <mesh scale={
        warningLevel === 'RED' ? [0.52, 3.1, 0.52] : [0.32, 1.55, 0.32]
      }>
        <sphereGeometry args={[80, 16, 16]} />
        <meshBasicMaterial
          color={warningLevel === 'RED' ? "#ef4444" : "#ffffff"}
          wireframe={true}
          transparent opacity={0.3} blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </mesh>
    </group>
      <Trajectory focusSatId={focusSatId} satellites={satellites} color="#00ffff" timeOffsetMinutes={timeOffsetMinutes} />
      <Trajectory focusSatId={secondarySatId} satellites={satellites} color="#eab308" timeOffsetMinutes={timeOffsetMinutes} />
      {escapeTrajectory && escapeTrajectory.length > 0 && (
        <Line
          points={escapeTrajectory.map(p => new THREE.Vector3(p[0], p[2], -p[1]))}
          color="#00ffff"
          lineWidth={2.5}
          transparent
          opacity={0.9}
        />
      )}
    </>
  );
}

function Trajectory({ focusSatId, satellites, color = "#ff0a2a", timeOffsetMinutes }: { focusSatId?: string | null, satellites: SatelliteData[], color?: string, timeOffsetMinutes: number }) {
  const points = useMemo(() => {
    if (!focusSatId) return [];
    if (focusSatId === 'JWST-1') return [];
    const sat = satellites.find(s => s.id === focusSatId);
    if (!sat) return [];

    const pts: THREE.Vector3[] = [];
    const baseTime = initialTime + simElapsedTime + manualTimeOffset;

    for (let i = 0; i <= 100; i++) {
      const t = new Date(baseTime + i * 60000);
      const pv = satellite.propagate(sat.satrec, t);
      if (pv.position && typeof pv.position !== 'boolean') {
        const p = pv.position as satellite.EciVec3<number>;
        pts.push(new THREE.Vector3(p.x, p.z, -p.y));
      }
    }
    return pts;
  }, [focusSatId, satellites, timeOffsetMinutes]);

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
    const dist = camera.position.length();
    // Calculate world-space units per pixel (assuming average 1080p height and 45deg FOV)
    const visibleHeight = 2 * Math.tan((45 * Math.PI) / 360) * dist;
    const unitsPerPixel = visibleHeight / 1080;
    // Maintain a mathematically perfect 5-pixel click radius regardless of zoom
    const dynamicThreshold = Math.max(15, unitsPerPixel * 5);
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
  timeOffsetMinutes = 0,
  escapeTrajectory,
  warningLevel,
  isInfrared = false
}: {
  tleData: string[],
  filter: string,
  onSelectSat: (sat: SatelliteData) => void,
  focusSatId?: string | null,
  secondarySatId?: string | null,
  timeOffsetMinutes?: number,
  escapeTrajectory?: number[][] | null,
  warningLevel?: string | null
}) {
  manualTimeOffset = timeOffsetMinutes * 60000;
  const [autoRotate, setAutoRotate] = useState(true);
  const controlsRef = useRef<any>(null);

  return (
    <div className="w-full h-full relative cursor-crosshair">
      <Canvas
        camera={{ position: [0, 500, 7500], fov: 45, near: 1, far: 400000 }}
        gl={{ antialias: true, alpha: true, logarithmicDepthBuffer: true }}
      >
        <DynamicRaycaster />
        <PhysicsManager autoRotate={autoRotate} setAutoRotate={setAutoRotate} />

        <ambientLight intensity={1.5} color={0x404040} />
        <directionalLight position={[50000, 20000, 30000]} intensity={2.5} color={0xffffff} />

        <Stars radius={10000} depth={200000} count={20000} factor={3} saturation={0} />

        <Earth />

        <Satellites
          tleData={tleData}
          filter={filter}
          onSelectSat={onSelectSat}
          focusSatId={focusSatId}
          secondarySatId={secondarySatId}
          controlsRef={controlsRef}
          timeOffsetMinutes={timeOffsetMinutes}
          escapeTrajectory={escapeTrajectory}
          warningLevel={warningLevel}
        />

        {focusSatId === 'JWST-1' && (
          <group position={[150000, 0, 0]}>
            <mesh rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[200, 200, 20, 6]} />
              <meshStandardMaterial color="#ffcc00" metalness={0.8} roughness={0.2} />
            </mesh>
            <pointLight distance={10000} intensity={2} color="#ffcc00" />
          </group>
        )}



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
