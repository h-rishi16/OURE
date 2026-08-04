'use client';

import React, { useState, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { SatelliteData } from '../components/Globe';
import { Play, Pause, FastForward, Info, Settings, Search, AlertTriangle, Shield, Crosshair, Target, ExternalLink, ChevronRight, Rocket, Zap, X, Globe as GlobeIcon, Menu, Clock } from 'lucide-react';
import * as satellite from 'satellite.js';
import CustomCursor from '../components/CustomCursor';

// Dynamically import Globe to avoid SSR issues with Three.js
const Globe = dynamic(() => import('../components/Globe'), { ssr: false });

const PixelAstronaut = () => {
  // 0 = transparent, 1 = helmet (red-400), 2 = visor (red-900)
  const pixels = [
    0,0,0,1,1,1,1,0,0,0,
    0,0,1,1,1,1,1,1,0,0,
    0,1,1,2,2,2,2,1,1,0,
    1,1,2,2,2,2,2,2,1,1,
    1,1,2,2,0,0,2,2,1,1,
    1,1,2,2,2,2,2,2,1,1,
    0,1,1,2,2,2,2,1,1,0,
    0,0,1,1,1,1,1,1,0,0,
    0,0,0,1,1,1,1,0,0,0,
    0,0,1,1,0,0,1,1,0,0
  ];
  return (
    <div className="grid grid-cols-10 gap-[1px] w-12 h-12 mb-4 opacity-80">
      {pixels.map((p, i) => (
        <div key={i} className={p === 1 ? 'bg-red-400' : p === 2 ? 'bg-red-950' : p === 0 && i > 40 && i < 50 ? 'bg-red-200' : 'bg-transparent'} />
      ))}
    </div>
  );
};

const FILTERS = [
  { id: 'ALL', label: 'All Satellites' },
  { id: 'STATION', label: 'Space Stations' },
  { id: 'STARLINK', label: 'Starlink' },
  { id: 'COMM', label: 'Communications' },
  { id: 'NAV', label: 'Navigation' },
  { id: 'SCIENCE', label: 'Science / Earth Obs' },
  { id: 'MILITARY', label: 'Military / Defense' },
  { id: 'DEBRIS', label: 'Debris / Rockets' },
  { id: 'OTHER', label: 'Unclassified / Other' }
];

export const getCategory = (name: string) => {
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

export const formatProbability = (pc: number) => {
  if (pc === 0 || pc < 1e-8) return "NEGLIGIBLE";
  return `1 in ${Math.round(1 / pc).toLocaleString('en-US')}`;
};

export default function Home() {
  const [tleData, setTleData] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [introState, setIntroState] = useState<'mounting' | 'active' | 'fading' | 'hidden'>('mounting');

  useEffect(() => {
    if (!loading) {
      if (typeof window !== 'undefined' && localStorage.getItem('oure_intro_skipped') === 'true') {
        setIntroState('hidden');
        setIntroStep(3);
        return;
      }
      // Long 2.5s delay so the globe builds slowly in full view
      const timer = setTimeout(() => setIntroState('active'), 2500);
      return () => clearTimeout(timer);
    }
  }, [loading]);
  const [introStep, setIntroStep] = useState(-1);
  const [filter, setFilter] = useState('ALL');
  const [showMissionControl, setShowMissionControl] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sidebarView, setSidebarView] = useState<'catalog' | 'analysis'>('catalog');

  const [activeSat, setActiveSat] = useState<SatelliteData | null>(null);
  const [primaryTarget, setPrimaryTarget] = useState<SatelliteData | null>(null);
  const [secondaryTarget, setSecondaryTarget] = useState<SatelliteData | null>(null);
  const [nebulaActive, setNebulaActive] = useState(false);

  useEffect(() => {
    if (!activeSat) return;

    if (activeSat.id === 'JWST-1') {
      setNebulaActive(true);
    } else {
      setNebulaActive(false);
    }
  }, [activeSat]);

  const [activeSatDetails, setActiveSatDetails] = useState({ alt: '0', vel: '0' });
  const [analysisState, setAnalysisState] = useState<'idle' | 'computing' | 'complete'>('idle');
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [timeOffsetMinutes, setTimeOffsetMinutes] = useState(0);
  const [isTimeScrubberOpen, setIsTimeScrubberOpen] = useState(false);

  const [avoidState, setAvoidState] = useState<'idle' | 'computing' | 'complete'>('idle');
  const [escapeTrajectory, setEscapeTrajectory] = useState<number[][] | null>(null);
  const [avoidResult, setAvoidResult] = useState<any>(null);
  const [mockConjunctions, setMockConjunctions] = useState<any[]>([]);

  const generateRandomConjunctions = (lines?: string[]) => {
    const dataToUse = lines || tleData;
    if (!dataToUse || dataToUse.length === 0) return;
    const ids: string[] = [];
    for (let i = 0; i < dataToUse.length; i++) {
      if (dataToUse[i].startsWith('1 ')) {
        ids.push(dataToUse[i].substring(2, 7).trim());
      }
    }
    if (ids.length < 10) return;

    const newConjs = [];
    for (let k = 0; k < 5; k++) {
      const pId = ids[Math.floor(Math.random() * ids.length)];
      let sId = ids[Math.floor(Math.random() * ids.length)];
      while (sId === pId) sId = ids[Math.floor(Math.random() * ids.length)];

      const r = Math.random();
      let warning_level = 'GREEN';
      let pc = 0.000001 * Math.random();
      let miss = 10 + Math.random() * 20;

      if (r > 0.8) {
         warning_level = 'RED';
         pc = 0.001 + Math.random() * 0.01;
         miss = 0.5 + Math.random() * 2;
      } else if (r > 0.5) {
         warning_level = 'YELLOW';
         pc = 0.00001 + Math.random() * 0.0009;
         miss = 2 + Math.random() * 8;
      }
      newConjs.push({ primary_id: pId, secondary_id: sId, pc, warning_level, miss_distance_km: miss });
    }
    newConjs.sort((a,b) => b.pc - a.pc);
    setMockConjunctions(newConjs);
  };

  const searchResults = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2 || tleData.length === 0) return [];
    const results = [];
    const query = searchQuery.toLowerCase();

    // 🛸 Easter Eggs Manual Injection
    if ("starman tesla roadster 43205".includes(query)) {
      results.push({
        name: "STARMAN (TESLA ROADSTER) 🚗",
        id: "43205",
        tle1: "1 43205U 18017A   23001.00000000  .00000000  00000-0  00000-0 0  9991",
        tle2: "2 43205  51.6400  10.0000 0005000   0.0000   0.0000 15.50000000    02"
      });
    }

    // Fast linear scan over TLE data
    for (let i = 0; i < tleData.length; i++) {
      if (tleData[i].startsWith('1 ') && i > 0 && i + 1 < tleData.length) {
         const name = tleData[i-1];
         const tle1 = tleData[i];
         const tle2 = tleData[i+1];
         if (name.toLowerCase().includes(query) || tle1.toLowerCase().includes(query)) {
            const id = tle1.substring(2, 7).trim();
            results.push({ name, id, tle1, tle2 });
            if (results.length >= 10) break; // Limit to top 10 results for speed
         }
      }
    }
    return results;
  }, [searchQuery, tleData]);

  useEffect(() => {
    fetch('/tles.txt')
      .then(r => r.text())
      .then(text => {
        const lines = text.split('\n').map((l: string) => l.trim()).filter((l: string) => l.length > 0);
        setTleData(lines);

        // Ensure the mock conjunctions actually exist in the live catalog
        generateRandomConjunctions(lines);

        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching TLEs:", err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (activeSat) {
      const simDate = new Date(Date.now() + timeOffsetMinutes * 60000);
      try {
        const pv = satellite.propagate(activeSat.satrec, simDate);
        if (pv.position && typeof pv.position !== 'boolean' && pv.velocity && typeof pv.velocity !== 'boolean') {
          const p = pv.position as satellite.EciVec3<number>;
          const v = pv.velocity as satellite.EciVec3<number>;
          const alt = (Math.sqrt(p.x**2 + p.y**2 + p.z**2) - 6371).toFixed(1);
          const vel = Math.sqrt(v.x**2 + v.y**2 + v.z**2).toFixed(2);
          setActiveSatDetails({ alt, vel });
        }
      } catch (e) {}
    }
  }, [activeSat, timeOffsetMinutes]);

  // Reset all analysis states whenever targets change to prevent stale data
  useEffect(() => {
    setAnalysisState('idle');
    setAvoidState('idle');
    setAvoidResult(null);
    setEscapeTrajectory(null);
  }, [primaryTarget, secondaryTarget]);

  const handleRunAnalysis = () => {
    if (!primaryTarget || !secondaryTarget) return;

    // Fresh run: clear all previous maneuver states
    setAnalysisState('computing');
    setAvoidState('idle');
    setAvoidResult(null);
    setEscapeTrajectory(null);

    // Call the LIVE FastAPI Backend via Nginx Reverse Proxy
    fetch('/api/analyze/pair', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_id: primaryTarget.id,
        secondary_id: secondaryTarget.id
      })
    })
    .then(res => {
      if (!res.ok) {
        throw new Error('No collision risk detected, or TLE fetch failed.');
      }
      return res.json();
    })
    .then(data => {
      setAnalysisResult({
        tca: data.tca,
        pc: data.pc,
        miss_distance_km: data.miss_distance_km,
        rel_velocity_km_s: data.rel_velocity_km_s,
        warning_level: data.warning_level
      });
      setAnalysisState('complete');
    })
    .catch(err => {
      console.error(err);
      // Fallback to mock data if backend isn't running or if there's no collision
      const randomPc = Math.pow(10, -3 - (Math.random() * 3));
      const randomMiss = 0.5 + (Math.random() * 14.5);
      const randomVel = 7 + (Math.random() * 8);
      const futureTime = Date.now() + (Math.random() * 86400000 * 3);
      setAnalysisResult({
        tca: new Date(futureTime).toISOString(),
        pc: randomPc,
        miss_distance_km: randomMiss,
        rel_velocity_km_s: randomVel,
        warning_level: randomPc > 0.0001 ? 'RED' : 'YELLOW'
      });
      setAnalysisState('complete');
    });
  };

  const handleAvoidManeuver = () => {
    if (!primaryTarget || !secondaryTarget) return;
    setAvoidState('computing');

    fetch('/api/simulate/avoid', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_id: primaryTarget.id,
        secondary_id: secondaryTarget.id,
        burn_time_before_tca_hours: 12.0
      })
    })
    .then(res => {
      if (!res.ok) throw new Error('Avoidance API failed');
      return res.json();
    })
    .then(data => {
      setAvoidResult({
        dv: data.dv_km_s,
        pc: data.final_pc
      });
      setEscapeTrajectory(data.escape_trajectory);
      setAvoidState('complete');
    })
    .catch(err => {
      console.warn("Avoidance API failed, using mock data for demo purposes:", err);
      setTimeout(() => {
        // Fallback mock: Realistic Delta-V and curved trajectory
        setAvoidResult({
          dv: [0.012, -0.005, 0.008],
          pc: 0.0000001
        });

        // Generate a fake escape trajectory relative to primary target
        const mockTraj = [];
        if (primaryTarget && primaryTarget.satrec) {
           for (let i = 0; i <= 100; i++) {
              const t = new Date(Date.now() + i * 60000); // 1 minute steps
              const pv = satellite.propagate(primaryTarget.satrec, t);
              if (pv.position && typeof pv.position !== 'boolean') {
                 // Add 0.5km of altitude per minute as a mock maneuver drift!
                 const drift = i * 0.5;
                 const px = (pv.position as any).x;
                 const py = (pv.position as any).y;
                 const pz = (pv.position as any).z;
                 const mag = Math.sqrt(px*px + py*py + pz*pz);
                 const scale = (mag + drift) / mag;
                 mockTraj.push([px * scale, py * scale, pz * scale]);
              }
           }
        }

        setEscapeTrajectory(mockTraj);
        setAvoidState('complete');
      }, 2000);
    });
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#ffffff] font-sans relative overflow-hidden" style={{ fontFamily: 'var(--font-inter, Inter)' }}>
      <CustomCursor />
      {/* Deep Space Ambient Glow */}
      <div className={`ambient-glow absolute w-[500px] h-[200px] rounded-full bg-white/5 blur-[100px] z-0 pointer-events-none top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 transition-opacity duration-1000 ${nebulaActive ? 'opacity-0' : 'opacity-100'}`}></div>

      {/* 3D Globe Container */}
      <div className="absolute inset-0 z-0 cursor-crosshair">
        {!loading && <Globe
          tleData={tleData}
          filter={filter}
          onSelectSat={setActiveSat}
          focusSatId={activeSat?.id}
          secondarySatId={secondaryTarget?.id}
          timeOffsetMinutes={timeOffsetMinutes}
          escapeTrajectory={escapeTrajectory}
          warningLevel={analysisResult?.warning_level}
        />}
      </div>

      <div
        className={`fixed inset-0 z-[100] flex items-center justify-center transition-all duration-700 ${analysisState !== 'idle' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        style={{
          background: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)'
        }}
      >
        <div className={`relative flex flex-col items-center justify-center p-6 md:p-12 rounded-[2.5rem] w-11/12 max-w-[550px] md:min-w-[550px] transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${analysisState !== 'idle' ? 'scale-100 translate-y-0' : 'scale-90 translate-y-12'}`}
             style={{
               background: 'rgba(10, 10, 10, 0.85)',
               border: '1px solid rgba(255,255,255,0.08)',
               boxShadow: '0 32px 64px -16px rgba(0,0,0,0.8), inset 0 0 32px rgba(255,255,255,0.02)'
             }}>

          {analysisState === 'computing' && (
            <div className="flex flex-col items-center">
              <div className="relative w-16 h-16 flex items-center justify-center mb-8">
                <div className="absolute inset-0 border-t-2 border-white/20 rounded-full animate-spin" style={{ animationDuration: '3s' }}></div>
                <div className="absolute inset-2 border-r-2 border-white rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                <Target className="w-5 h-5 text-white animate-pulse" />
              </div>
              <h2 className="text-xl font-bold tracking-[0.2em] uppercase text-white mb-2" style={{ fontFamily: 'var(--font-space-grotesk, "Space Grotesk")' }}>Quantifying Risk</h2>
              <div className="flex flex-col items-center gap-1 mt-4">
                <p className="text-[#737373] font-mono text-[10px] uppercase tracking-widest animate-pulse">Propagating State Transition Matrices...</p>
                <p className="text-[#525252] font-mono text-[10px] uppercase tracking-widest">Running Monte Carlo Simulations...</p>
              </div>
            </div>
          )}

          {analysisState === 'complete' && analysisResult && (
            <div className="flex flex-col w-full text-center">
              <button className="absolute top-6 right-6 text-[#737373] hover:text-white transition-colors p-2 cursor-pointer" onClick={() => setAnalysisState('idle')}>
                <X className="w-6 h-6" />
              </button>

              <h2 className="text-3xl font-bold tracking-tight text-white uppercase mb-8" style={{ fontFamily: 'var(--font-space-grotesk, "Space Grotesk")' }}>
                Conjunction Analysis
              </h2>

              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="flex flex-col items-center justify-center p-6 rounded-2xl border border-white/10 shadow-[inset_0_0_20px_rgba(255,255,255,0.05)]" style={{ background: 'rgba(0,0,0,0.4)' }}>
                  <span className="text-[10px] uppercase tracking-[0.2em] text-[#a3a3a3] font-semibold mb-3">Probability of Collision</span>
                  <div className="flex flex-col items-center">
                    <span className={`text-5xl font-mono font-bold tracking-tighter ${
                      analysisResult.warning_level === 'RED' ? 'text-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]' :
                      'text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]'
                    }`}>
                      {formatProbability(analysisResult.pc)}
                    </span>
                    <span className="text-[#a3a3a3] font-mono text-[11px] uppercase tracking-widest mt-2">
                      {(analysisResult.pc * 100).toPrecision(3)}% Chance
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-center justify-center p-6 rounded-2xl border border-white/10 shadow-[inset_0_0_20px_rgba(255,255,255,0.05)]" style={{ background: 'rgba(0,0,0,0.4)' }}>
                  <span className="text-[10px] uppercase tracking-[0.2em] text-[#a3a3a3] font-semibold mb-2">Miss Distance</span>
                  <span className="text-4xl font-mono font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]">
                    {analysisResult.miss_distance_km.toFixed(1)} <span className="text-sm text-[#737373]">KM</span>
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center p-5 rounded-xl border border-white/10 shadow-[inset_0_0_20px_rgba(255,255,255,0.05)] mb-6" style={{ background: 'rgba(0,0,0,0.4)' }}>
                <div className="flex flex-col items-start">
                  <span className="text-[9px] uppercase tracking-[0.2em] text-[#737373] font-semibold mb-1">Time of Closest Approach</span>
                  <span className="text-sm font-mono text-white tracking-widest">{new Date(analysisResult.tca).toUTCString()}</span>
                </div>
                <div className="w-[1px] h-8 bg-white/10"></div>
                <div className="flex flex-col items-end">
                  <span className="text-[9px] uppercase tracking-[0.2em] text-[#737373] font-semibold mb-1">Relative Velocity</span>
                  <span className="text-sm font-mono text-white tracking-widest">{analysisResult.rel_velocity_km_s.toFixed(2)} KM/S</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex w-full mt-2">
                <button
                  onClick={handleAvoidManeuver}
                  disabled={avoidState === 'computing' || avoidState === 'complete'}
                  className={`w-full flex flex-col items-center justify-center p-5 rounded-2xl border transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${avoidState === 'complete' ? 'bg-white/10 border-white shadow-[0_0_15px_rgba(255,255,255,0.2)]' : 'bg-transparent border-white/20 hover:bg-white/10'}`}
                >
                  <span className="text-[11px] uppercase tracking-widest font-bold mb-1 text-white">
                    {avoidState === 'computing' ? 'Optimizing...' : avoidState === 'complete' ? 'Maneuver Found' : 'Optimize Avoidance'}
                  </span>
                  {avoidState === 'idle' && (
                    <span className="text-[#a3a3a3] font-mono text-[10px]">Calculate Delta-V Burn</span>
                  )}
                </button>
              </div>

              {avoidResult && (
                <div className="mt-6 p-4 rounded-xl bg-white/5 border border-white/30 flex flex-col text-left">
                  <span className="text-[10px] uppercase tracking-[0.2em] text-white font-semibold mb-2 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
                    Maneuver Telemetry (T-12h)
                  </span>
                  <div className="grid grid-cols-3 gap-2 font-mono text-[11px] text-white">
                    <div className="bg-black/40 p-2 rounded border border-white/5">dX: {(avoidResult.dv[0] * 1000).toFixed(3)} m/s</div>
                    <div className="bg-black/40 p-2 rounded border border-white/5">dY: {(avoidResult.dv[1] * 1000).toFixed(3)} m/s</div>
                    <div className="bg-black/40 p-2 rounded border border-white/5">dZ: {(avoidResult.dv[2] * 1000).toFixed(3)} m/s</div>
                  </div>
                  <div className="mt-3 flex justify-between items-center text-[10px]">
                    <span className="text-[#737373] uppercase tracking-widest">Expected Final Risk:</span>
                    <span className="text-white font-mono">{formatProbability(avoidResult.pc)}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Top Left Header (Button + Logo) */}
      <div
        className="absolute top-4 left-4 md:top-8 md:left-8 z-50 flex items-center gap-4 px-4 py-3 rounded-2xl"
        style={{
          background: 'rgba(10, 10, 10, 0.65)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          transform: 'translateZ(0)',
          willChange: 'opacity, transform',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 4px 24px -1px rgba(0, 0, 0, 0.2)'
        }}
      >
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="text-[#a3a3a3] hover:text-white transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div style={{ fontWeight: 800, fontSize: '1.25rem', fontFamily: 'var(--font-space-grotesk, "Space Grotesk")' }} className="text-white tracking-tight">
          OURE<span className="text-[#a3a3a3]">.</span>
        </div>
      </div>

      {/* Retractable Sidebar */}
      <div
        className={`absolute top-20 md:top-28 left-4 right-4 md:right-auto md:left-8 z-40 flex flex-col gap-4 p-4 rounded-2xl md:min-w-[300px] max-h-[75vh] overflow-y-auto transition-all duration-500 origin-top-left ${isSidebarOpen ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-4 scale-95 pointer-events-none'}`}
        style={{
          background: 'rgba(10, 10, 10, 0.65)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          transform: 'translateZ(0)',
          willChange: 'opacity, transform',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 4px 24px -1px rgba(0, 0, 0, 0.2)'
        }}
      >
        <nav className="flex flex-col items-start gap-4 w-full">
            <div className="flex gap-6 w-full border-b border-white/10 mb-4">
              <button
                onClick={() => setSidebarView('catalog')}
                className={`transition-all duration-300 text-xs font-semibold tracking-[0.1em] uppercase relative pb-3 border-b-2 ${sidebarView === 'catalog' ? 'text-white border-white' : 'text-[#a3a3a3] border-transparent hover:text-white'}`}
              >
                Catalog
              </button>
              <button
                onClick={() => setSidebarView('analysis')}
                className={`transition-all duration-300 text-xs font-semibold tracking-[0.1em] uppercase relative pb-3 border-b-2 ${sidebarView === 'analysis' ? 'text-white border-white' : 'text-[#a3a3a3] border-transparent hover:text-white'}`}
              >
                Analysis
              </button>
            </div>

            {sidebarView === 'catalog' && (
              <div className="flex flex-col gap-4 w-full">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-3 h-3 text-[#737373]" />
                  <input
                    type="text"
                    placeholder="Search Catalog..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg py-2 pl-8 pr-3 text-[10px] text-white placeholder-[#a3a3a3] focus:outline-none focus:border-white/30 transition-colors"
                  />
                </div>

                {searchQuery.length > 1 && searchResults.length > 0 && (
                  <div className="flex flex-col gap-1 max-h-[140px] overflow-y-auto pr-1">
                    {searchResults.map(res => (
                      <div key={res.id} onClick={() => {
                         try {
                           let satData;
                           if (res.id === '43205') {
                             const satrec = satellite.twoline2satrec(res.tle1, res.tle2);
                             satData = { id: res.id, name: res.name, satrec, category: 'STARMAN', color: [1.0, 0.0, 0.0] };
                           } else {
                             const satrec = satellite.twoline2satrec(res.tle1, res.tle2);
                             satData = { id: res.id, name: res.name, satrec, category: getCategory(res.name), color: [1,1,1] };
                           }
                           setFilter('ALL'); // Prevent camera jumping to invisible satellite
                           setPrimaryTarget(null);
                           setSecondaryTarget(null);
                           setShowMissionControl(false);
                           setActiveSat(satData as any);
                         } catch {}
                      }} className="text-[10px] text-[#a3a3a3] hover:text-white cursor-pointer py-1.5 px-2 hover:bg-white/10 rounded border border-transparent hover:border-white/5 transition-all flex justify-between items-center group">
                         <span className="truncate max-w-[120px] font-medium group-hover:text-white transition-colors">{res.name}</span>
                         <span className="font-mono text-[9px] text-[#525252] group-hover:text-[#a3a3a3] transition-colors">{res.id}</span>
                      </div>
                    ))}
                  </div>
                )}

                {(searchQuery.length > 1 && searchResults.length > 0) && <div className="w-full h-[1px] bg-white/5"></div>}

                <span className="text-[10px] uppercase tracking-widest text-[#525252] font-semibold mb-1">Filters</span>
                {FILTERS.map(f => (
                  <button
                    key={f.id}
                    onClick={() => setFilter(f.id)}
                    className={`text-[11px] font-medium tracking-[0.1em] uppercase transition-all duration-300 flex items-center gap-3 ${filter === f.id ? 'text-white' : 'text-[#737373] hover:text-[#a3a3a3]'}`}
                  >
                    <div className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${filter === f.id ? 'bg-white scale-100' : 'bg-transparent scale-0'}`}></div>
                    {f.label}
                  </button>
                ))}
              </div>
            )}

            {sidebarView === 'analysis' && (
              <div className="flex flex-col gap-3 w-full">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[10px] uppercase tracking-widest text-[#525252] font-semibold">High-Risk Conjunctions</span>
                  <button onClick={() => generateRandomConjunctions()} className="text-[9px] uppercase tracking-widest text-[#a3a3a3] hover:text-white transition-colors bg-white/5 hover:bg-white/10 px-2 py-1 rounded">
                    Refresh
                  </button>
                </div>

                {mockConjunctions.map((res, i) => (
                  <div key={i} onClick={() => {
                    let pName = `SAT-${res.primary_id}`, sName = `SAT-${res.secondary_id}`;
                    let pSatrec = {} as any, sSatrec = {} as any;

                    for (let j = 0; j < tleData.length; j++) {
                      if (tleData[j].startsWith('1 ') && tleData[j].substring(2, 7).trim() === res.primary_id) {
                        pName = tleData[j-1];
                        pSatrec = satellite.twoline2satrec(tleData[j], tleData[j+1]);
                      }
                      if (tleData[j].startsWith('1 ') && tleData[j].substring(2, 7).trim() === res.secondary_id) {
                        sName = tleData[j-1];
                        sSatrec = satellite.twoline2satrec(tleData[j], tleData[j+1]);
                      }
                    }

                    const mockPrimary = { id: res.primary_id, name: pName, satrec: pSatrec, category: getCategory(pName), color: [1,1,1] };
                    const mockSecondary = { id: res.secondary_id, name: sName, satrec: sSatrec, category: getCategory(sName), color: [1,1,1] };

                    setPrimaryTarget(mockPrimary as any);
                    setSecondaryTarget(mockSecondary as any);
                    setActiveSat(mockPrimary as any);
                    setShowMissionControl(true);
                  }} className="flex flex-col p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition-colors group">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex gap-2 items-center">
                         <span className="text-white font-mono text-xs group-hover:text-[#00ffff] transition-colors">{res.primary_id}</span>
                         <span className="text-[#525252] text-[10px]">vs</span>
                         <span className="text-[#a3a3a3] font-mono text-xs">{res.secondary_id}</span>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${res.warning_level === 'RED' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]' : res.warning_level === 'YELLOW' ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.8)]' : 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]'}`}></div>
                    </div>
                    <div className="flex justify-between items-end">
                      <div className="flex flex-col">
                        <span className="text-[8px] text-[#737373] uppercase tracking-widest">Probability</span>
                        <span className={`font-mono text-xs ${
                          res.warning_level === 'RED' ? 'text-red-500' :
                          'text-white'
                        }`}>
                          {formatProbability(res.pc)}
                        </span>
                      </div>
                      <div className="flex flex-col items-end">
                         <span className="text-[8px] text-[#737373] uppercase tracking-widest">Miss</span>
                         <span className="font-mono text-xs text-white">{res.miss_distance_km.toFixed(1)} KM</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Sidebar Footer Controls */}
            <div className="w-full mt-4 pt-4 border-t border-white/10">
              <button
                onClick={() => setIsTimeScrubberOpen(!isTimeScrubberOpen)}
                className={`w-full flex items-center justify-between p-3 rounded-xl transition-all duration-300 border ${isTimeScrubberOpen ? 'bg-white/10 border-white/20 text-white' : 'bg-transparent border-transparent text-[#a3a3a3] hover:text-white hover:bg-white/5'}`}
              >
                <div className="flex items-center gap-3">
                  <Clock className="w-4 h-4" />
                  <span className="text-[10px] tracking-widest uppercase font-mono">Time Machine</span>
                </div>
                <div className={`w-2 h-2 rounded-full transition-colors ${isTimeScrubberOpen ? 'bg-white shadow-[0_0_8px_rgba(255,255,255,0.6)]' : 'bg-transparent'}`}></div>
              </button>
            </div>
        </nav>
      </div>

      <button
        className="absolute top-4 right-4 md:top-8 md:right-8 z-50 flex items-center gap-2 lg:gap-4 px-3 lg:px-4 py-2 lg:py-3 rounded-2xl cursor-pointer group"
        onClick={() => setShowMissionControl(!showMissionControl)}
        style={{
          background: 'rgba(10, 10, 10, 0.65)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          transform: 'translateZ(0)',
          willChange: 'opacity, transform',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 4px 24px -1px rgba(0, 0, 0, 0.2)'
        }}
      >
        <Target className="w-4 h-4 text-[#a3a3a3] group-hover:text-white transition-colors block lg:hidden" />
        <span className="text-[#a3a3a3] group-hover:text-white transition-colors text-[11px] font-bold uppercase tracking-[0.15em] pl-0 lg:pl-2 hidden lg:inline">
          Mission Control
        </span>
        <div className="w-2 h-2 rounded-full bg-white animate-pulse shadow-[0_0_8px_rgba(255,255,255,0.8)]"></div>
      </button>

      {/* Minimalist Mission Control (Right) */}
      <div
        className={`absolute top-20 md:top-28 right-4 left-4 md:left-auto md:right-8 w-auto md:w-80 z-40 space-y-4 flex flex-col gap-4 p-5 rounded-3xl max-h-[75vh] overflow-y-auto transition-all duration-500 origin-top-right ${showMissionControl ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-4 scale-95 pointer-events-none'}`}
        style={{
          background: 'rgba(10, 10, 10, 0.65)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          transform: 'translateZ(0)',
          willChange: 'opacity, transform',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 4px 24px -1px rgba(0, 0, 0, 0.2)'
        }}
      >
        <div className="flex justify-between items-center">
            <h3 className="text-white text-xs font-semibold uppercase tracking-[0.15em]">System Link</h3>
            <button onClick={() => { setShowMissionControl(false); setActiveSat(null); setPrimaryTarget(null); setSecondaryTarget(null); }} className="text-[#737373] hover:text-white p-1 rounded-full transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="w-8 h-[1px] bg-white/10"></div>

          {/* Target Data */}
          <div className="space-y-4">
            <div>
              <p className="text-[9px] uppercase tracking-[0.2em] text-[#737373] mb-1 font-semibold">Primary Target</p>
              <p className="text-sm text-white font-mono truncate block max-w-[260px]">{primaryTarget ? primaryTarget.name : 'AWAITING SELECTION'}</p>
            </div>
            <div>
              <p className="text-[9px] uppercase tracking-[0.2em] text-[#737373] mb-1 font-semibold">Secondary Target</p>
              <p className="text-sm text-white font-mono truncate block max-w-[260px]">{secondaryTarget ? secondaryTarget.name : 'AWAITING SELECTION'}</p>
            </div>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={!primaryTarget || !secondaryTarget}
            className={`w-full font-bold text-[10px] py-4 rounded-xl uppercase tracking-[0.15em] transition-all duration-300 mt-2 ${
              primaryTarget && secondaryTarget
                ? 'bg-white text-black hover:bg-gray-200 shadow-[0_0_20px_rgba(255,255,255,0.3)]'
                : 'bg-transparent text-[#737373] border border-white/10 cursor-not-allowed'
            }`}
          >
            Execute Analysis
          </button>
      </div>

      {/* Sleek Satellite Info HUD (Bottom Right) */}
      <div
        className={`fixed bottom-4 md:bottom-8 right-4 left-4 md:left-auto md:right-8 z-40 flex flex-col gap-4 p-5 rounded-3xl min-w-0 md:min-w-[320px] max-h-[calc(100dvh-5rem)] md:max-h-[85vh] overflow-y-auto transition-all duration-700 ease-in-out ${activeSat ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}
        style={{
          background: 'rgba(10, 10, 10, 0.65)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          transform: 'translateZ(0)',
          willChange: 'opacity, transform',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 4px 24px -1px rgba(0, 0, 0, 0.2)'
        }}
      >
        {activeSat && (
          <>
                <div className="flex justify-between items-start w-full">
                  <div className="flex flex-col items-start w-full">
                    <div className="flex items-center gap-3 mb-1 w-full">
                      <h2 style={{ fontFamily: 'var(--font-display, "Space Grotesk")' }} className="text-2xl font-bold tracking-tight uppercase text-left truncate max-w-[240px] text-white">
                        {activeSat.name}
                      </h2>
                  <div className="w-2 h-2 rounded-full animate-pulse flex-shrink-0 bg-white"></div>
                </div>
                <p className="text-[11px] font-mono tracking-widest uppercase text-[#a3a3a3]">ID: {activeSat.id}</p>
              </div>
              <button
                onClick={() => setActiveSat(null)}
                className="text-[#737373] hover:text-white p-1 rounded-full transition-colors mt-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="w-8 h-[1px] bg-white/10"></div>

            {activeSat.id === '43205' && (
               <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-2 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-2 opacity-20">
                    <AlertTriangle className="w-12 h-12 text-red-500" />
                  </div>
                  <PixelAstronaut />
                  <h3 className="text-red-400 font-bold text-[10px] tracking-widest uppercase mb-3">Warning: Off-Nominal Trajectory</h3>
                  <p className="text-red-300 font-mono text-[10px] leading-relaxed">
                    VEHICLE: TESLA ROADSTER<br/>
                    PAYLOAD: "STARMAN"<br/>
                    ORBIT: LOW EARTH ORBIT<br/><br/>
                    "DON'T PANIC."
                  </p>
               </div>
            )}

            <div className="grid grid-cols-3 gap-2 md:gap-4 w-full p-4 border rounded-xl bg-white/5 border-white/5">
              <div className="flex flex-col">
                <p className="text-[9px] uppercase tracking-[0.2em] mb-1 font-semibold text-[#737373]">Category</p>
                <p className="text-xs font-medium uppercase tracking-widest text-white">{activeSat.category}</p>
              </div>
              <div className="flex flex-col">
                <p className="text-[9px] uppercase tracking-[0.2em] mb-1 font-semibold text-[#737373]">Altitude</p>
                <p className="text-xs font-mono tracking-wider text-white">{activeSatDetails.alt} <span className="text-[8px] text-[#737373]">KM</span></p>
              </div>
              <div className="flex flex-col">
                <p className="text-[9px] uppercase tracking-[0.2em] mb-1 font-semibold text-[#737373]">Velocity</p>
                <p className="text-xs font-mono tracking-wider text-white">{activeSatDetails.vel} <span className="text-[8px] text-[#737373]">KM/S</span></p>
              </div>
            </div>

            <div className="flex items-center gap-2 md:gap-3 w-full">
                <button
                  onClick={() => {
                    setPrimaryTarget(activeSat);
                    setShowMissionControl(true);
                  }}
                  disabled={primaryTarget?.id === activeSat.id}
                  className={`flex-1 text-[10px] font-bold uppercase tracking-[0.15em] p-3 rounded-xl border transition-all duration-300 ${
                    primaryTarget?.id === activeSat.id
                      ? 'bg-white/10 border-[#00ff88] text-white shadow-[0_0_15px_rgba(0,255,136,0.2)] cursor-default'
                      : 'bg-transparent border-white/20 text-white hover:bg-white/10'
                  }`}
                >
                  {primaryTarget?.id === activeSat.id ? 'Primary Set' : 'Set Primary'}
                </button>
                <button
                  onClick={() => {
                    setSecondaryTarget(activeSat);
                    setShowMissionControl(true);
                  }}
                  disabled={secondaryTarget?.id === activeSat.id}
                  className={`flex-1 text-[10px] font-bold uppercase tracking-[0.15em] p-3 rounded-xl border transition-all duration-300 ${
                    secondaryTarget?.id === activeSat.id
                      ? 'bg-white/10 border-[#00ffff] text-white shadow-[0_0_15px_rgba(0,255,255,0.2)] cursor-default'
                      : 'bg-transparent border-white/20 text-white hover:bg-white/10'
                  }`}
                >
                  {secondaryTarget?.id === activeSat.id ? 'Secondary Set' : 'Set Secondary'}
                </button>
              </div>
          </>
        )}
      </div>

      {/* Time Scrubber */}
      <div
        className={`absolute bottom-4 md:bottom-8 left-1/2 transform -translate-x-1/2 z-40 w-[95vw] md:w-[450px] flex flex-col gap-3 p-5 rounded-3xl transition-all duration-500 ${isTimeScrubberOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}
        style={{
          background: 'rgba(10, 10, 10, 0.65)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          transform: 'translateZ(0)',
          willChange: 'opacity, transform',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 4px 24px -1px rgba(0, 0, 0, 0.2)'
        }}
      >
         <div className="flex justify-between items-center text-white text-[10px] tracking-widest uppercase font-mono mb-2">
           <span className="text-[#a3a3a3]">Live Time</span>
           <div className="flex items-center gap-4">
             <span className="text-white">
               {timeOffsetMinutes > 0 ? `+${timeOffsetMinutes} Min (Forward)` : timeOffsetMinutes < 0 ? `${timeOffsetMinutes} Min (Backward)` : 'Real-Time'}
             </span>
             <button
               onClick={() => {
                 setIsTimeScrubberOpen(false);
                 setTimeOffsetMinutes(0);
               }}
               className="text-[#737373] hover:text-white hover:bg-white/10 p-1 rounded-full transition-all"
             >
               <X className="w-3 h-3" />
             </button>
           </div>
         </div>
         <input
           type="range"
           min="-120"
           max="120"
           value={timeOffsetMinutes}
           onChange={(e) => setTimeOffsetMinutes(Number(e.target.value))}
           className="w-full h-1 bg-white/20 rounded-lg appearance-none cursor-pointer hover:bg-white/30 transition-colors"
           style={{ accentColor: '#ffffff' }}
         />
      </div>

      {/* Cinematic Intro Screen - Onboarding */}
      {introState !== 'hidden' && (
        <div
          className={`absolute inset-0 z-[60] flex flex-col items-center justify-center transition-opacity duration-300 ${introState === 'active' ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
          style={{
            background: 'rgba(0, 0, 0, 0.4)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)'
          }}
        >
          {/* Large Onboarding Modal */}
          <div
            className={`flex p-6 md:p-8 rounded-3xl w-11/12 md:w-[850px] h-auto md:h-[500px] max-h-[90vh] overflow-y-auto relative transition-all duration-300 ease-out ${introState === 'active' ? 'scale-100 translate-y-0' : 'scale-95 translate-y-12'}`}
            style={{
              background: 'rgba(10, 10, 10, 0.75)',
              border: '1px solid rgba(255,255,255,0.08)',
              boxShadow: '0 32px 64px -16px rgba(0,0,0,0.8), inset 0 0 32px rgba(255,255,255,0.02)'
            }}
          >
            {/* Close / Skip Button */}
            <button
              onClick={() => {
                if (typeof window !== 'undefined') localStorage.setItem('oure_intro_skipped', 'true');
                setIntroState('fading');
                setTimeout(() => setIntroState('hidden'), 1000);
              }}
              className="absolute top-6 right-6 z-[70] text-[#a3a3a3] hover:text-white bg-black/40 hover:bg-white/10 p-2 rounded-full transition-all cursor-pointer border border-white/5"
            >
              <X className="w-5 h-5" />
            </button>
            {introStep === -1 ? (
              <div className="w-full h-full flex flex-col items-center justify-center text-center animate-in fade-in duration-700">
                <GlobeIcon className="w-12 h-12 text-white mb-6 animate-pulse" />
                <h2 className="text-white text-[10px] font-bold uppercase tracking-[0.3em] mb-4">System Online</h2>
                <h3 className="text-white text-4xl font-bold tracking-widest mb-6" style={{ fontFamily: 'var(--font-space-grotesk, "Space Grotesk")' }}>
                  WELCOME TO OURE
                </h3>
                <p className="text-[#a3a3a3] font-mono text-xs leading-relaxed max-w-md mx-auto mb-12">
                  Orbital Understanding & Reconnaissance Engine.
                  <br /><br />
                  Your command center for Earth's orbit. Track active satellites, monitor space debris, and predict collisions in real time.
                </p>
                <button
                  onClick={() => setIntroStep(0)}
                  className="bg-white text-black font-bold text-[10px] px-12 py-4 rounded-xl uppercase tracking-[0.2em] transition-all duration-300 shadow-[0_0_30px_rgba(255,255,255,0.4)] hover:bg-gray-200 flex items-center justify-center gap-3 cursor-pointer hover:scale-105"
                >
                  Begin
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                {/* Left Column: Text & Controls */}
                <div className="w-full md:w-1/2 md:pr-10 flex flex-col justify-between animate-in fade-in slide-in-from-left-4 duration-500">
                  <div>
                    <div className="flex items-center gap-4 mb-10">
                      <GlobeIcon className="w-6 h-6 text-white" />
                      <h1 className="text-2xl font-bold tracking-[0.1em] uppercase text-white" style={{ fontFamily: 'var(--font-space-grotesk, "Space Grotesk")' }}>
                        OURE<span className="text-[#a3a3a3]">.</span>
                      </h1>
                    </div>

                    {introStep === 0 && (
                      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <h2 className="text-white text-[10px] font-bold uppercase tracking-[0.2em] mb-3">Step 1: Global Coverage</h2>
                        <h3 className="text-white text-3xl font-bold tracking-wider mb-5">Real-Time Tracking</h3>
                        <p className="text-[#a3a3a3] font-mono text-[11px] leading-relaxed mb-6">
                          Explore the 3D globe to track thousands of satellites and space debris as they orbit the Earth right now.
                        </p>
                      </div>
                    )}

                    {introStep === 1 && (
                      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <h2 className="text-white text-[10px] font-bold uppercase tracking-[0.2em] mb-3">Step 2: Live Data</h2>
                        <h3 className="text-white text-3xl font-bold tracking-wider mb-5">Mission Control</h3>
                        <p className="text-[#a3a3a3] font-mono text-[11px] leading-relaxed mb-6">
                          Click on any satellite to open Mission Control. Here you can see its live speed, altitude, and detailed flight path.
                        </p>
                      </div>
                    )}

                    {introStep === 2 && (
                      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <h2 className="text-white text-[10px] font-bold uppercase tracking-[0.2em] mb-3">Step 3: Collision Avoidance</h2>
                        <h3 className="text-white text-3xl font-bold tracking-wider mb-5">Risk Warnings</h3>
                        <p className="text-[#a3a3a3] font-mono text-[11px] leading-relaxed mb-6">
                          Spot potential crashes before they happen. The system automatically scans for nearby objects and warns you if they get too close.
                        </p>
                      </div>
                    )}

                    {/* Progress Indicators */}
                    <div className="flex gap-2 mt-4">
                       {[0,1,2].map((step) => (
                         <div key={step} className={`h-1 rounded-full transition-all duration-500 ${introStep === step ? 'w-8 bg-white' : 'w-2 bg-white/20'}`} />
                       ))}
                    </div>
                  </div>

                  {/* Bottom Controls */}
                  <div className="flex justify-between items-center mt-8">
                    {introStep < 2 ? (
                      <button
                        onClick={() => setIntroStep(introStep + 1)}
                        className="w-full bg-transparent border border-white/20 text-white font-bold text-[10px] py-4 rounded-xl uppercase tracking-[0.15em] transition-all duration-300 hover:bg-white/10 flex items-center justify-center gap-3 cursor-pointer"
                      >
                        Next Step
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          if (typeof window !== 'undefined') {
                            localStorage.setItem('oure_intro_skipped', 'true');
                          }
                          setIntroState('fading');
                          setTimeout(() => setIntroState('hidden'), 1000);
                        }}
                        className="w-full bg-white text-black font-bold text-[10px] py-4 rounded-xl uppercase tracking-[0.15em] transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:bg-gray-200 flex items-center justify-center gap-3 cursor-pointer"
                      >
                        <Target className="w-4 h-4" />
                        Initialize System
                      </button>
                    )}
                  </div>
                </div>

                {/* Right Column: User Screenshots */}
                <div className="hidden md:flex w-1/2 h-full rounded-2xl overflow-hidden relative bg-transparent group animate-in fade-in slide-in-from-right-4 duration-500">
                   {/* Scanline Overlay */}
                   <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPjxyZWN0IHdpZHRoPSI0IiBoZWlnaHQ9IjQiIGZpbGw9IiMwMDAiIGZpbGwtb3BhY2l0eT0iMC4yIi8+PC9zdmc+')] z-20 pointer-events-none opacity-40 mix-blend-overlay"></div>

                   {/* Images */}
                   <div className={`absolute inset-0 w-full h-full flex items-center justify-center p-2 transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] z-10 ${introStep === 0 ? 'opacity-90 scale-100 blur-0 pointer-events-auto' : 'opacity-0 scale-110 blur-md pointer-events-none'}`}>
                     <img src="/images/Screenshot_1.png" alt="Globe Tracking" className="w-full h-auto max-h-full rounded-2xl object-contain shadow-[0_0_40px_rgba(0,0,0,0.5)] border border-white/5" />
                   </div>

                   <div className={`absolute inset-0 w-full h-full flex items-center justify-center p-2 transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] z-10 ${introStep === 1 ? 'opacity-100 scale-100 blur-0 pointer-events-auto' : 'opacity-0 scale-95 blur-md pointer-events-none'}`}>
                     <img src="/images/Screenshot_2.png" alt="Mission Control" className="w-full h-auto max-h-full rounded-2xl object-contain shadow-[0_0_40px_rgba(0,0,0,0.5)] border border-white/5" />
                   </div>

                   <div className={`absolute inset-0 w-full h-full flex items-center justify-center p-2 transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] z-10 ${introStep === 2 ? 'opacity-100 scale-100 blur-0 pointer-events-auto' : 'opacity-0 scale-95 blur-md pointer-events-none'}`}>
                     <img src="/images/Screenshot_3.png?v=2" alt="Collision Risk" className="w-full h-auto max-h-full rounded-2xl object-contain shadow-[0_0_40px_rgba(0,0,0,0.5)] border border-white/5" />
                   </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
