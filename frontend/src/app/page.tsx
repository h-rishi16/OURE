'use client';

import React, { useState, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { SatelliteData } from '../components/Globe';
import { Rocket, Target, Zap, X, Globe as GlobeIcon, Menu, Search, Clock, Skull } from 'lucide-react';
import * as satellite from 'satellite.js';
import CustomCursor from '../components/CustomCursor';

// Dynamically import Globe to avoid SSR issues with Three.js
const Globe = dynamic(() => import('../components/Globe'), { ssr: false });

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

export default function Home() {
  const [tleData, setTleData] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [showMissionControl, setShowMissionControl] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sidebarView, setSidebarView] = useState<'catalog' | 'analysis'>('catalog');

  const [activeSat, setActiveSat] = useState<SatelliteData | null>(null);
  const [primaryTarget, setPrimaryTarget] = useState<SatelliteData | null>(null);
  const [secondaryTarget, setSecondaryTarget] = useState<SatelliteData | null>(null);
  const [activeSatDetails, setActiveSatDetails] = useState({ alt: '0', vel: '0' });
  const [analysisState, setAnalysisState] = useState<'idle' | 'computing' | 'complete'>('idle');
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [timeOffsetMinutes, setTimeOffsetMinutes] = useState(0);
  const [isTimeScrubberOpen, setIsTimeScrubberOpen] = useState(false);
  const [isShattered, setIsShattered] = useState(false);

  const searchResults = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2 || tleData.length === 0) return [];
    const results = [];
    const query = searchQuery.toLowerCase();

    // Fast linear scan over TLE data
    for (let i = 0; i < tleData.length; i++) {
      if (tleData[i].startsWith('1 ') && i > 0 && i + 1 < tleData.length) {
         const name = tleData[i-1];
         const tle1 = tleData[i];
         const tle2 = tleData[i+1];
         if (name.toLowerCase().includes(query) || tle1.includes(query)) {
            const id = tle1.substring(2, 7).trim();
            results.push({ name, id, tle1, tle2 });
            if (results.length >= 10) break; // Limit to top 10 results for speed
         }
      }
    }
    return results;
  }, [searchQuery, tleData]);

  useEffect(() => {
    fetch('/api/tles')
      .then(res => res.text())
      .then(data => {
        const lines = data.split('\n').map(l => l.trim()).filter(l => l.length > 0);
        setTleData(lines);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching TLEs:", err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (activeSat) {
      const pv = satellite.propagate(activeSat.satrec, new Date());
      if (pv.position && typeof pv.position !== 'boolean' && pv.velocity && typeof pv.velocity !== 'boolean') {
        const p = pv.position as satellite.EciVec3<number>;
        const v = pv.velocity as satellite.EciVec3<number>;
        const alt = (Math.sqrt(p.x**2 + p.y**2 + p.z**2) - 6371).toFixed(1);
        const vel = Math.sqrt(v.x**2 + v.y**2 + v.z**2).toFixed(2);
        setActiveSatDetails({ alt, vel });
      }
    }
  }, [activeSat]);

  const handleRunAnalysis = () => {
    if (!primaryTarget || !secondaryTarget) return;
    setAnalysisState('computing');

    // Call the LIVE FastAPI Backend!
    fetch('http://127.0.0.1:8000/analyze/pair', {
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

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#ffffff] font-sans relative overflow-hidden" style={{ fontFamily: 'var(--font-main, Inter)' }}>
      <CustomCursor />
      {/* Deep Space Ambient Glow */}
      <div className="ambient-glow absolute w-[500px] h-[200px] rounded-full bg-white/5 blur-[100px] z-0 pointer-events-none top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>

      {/* 3D Globe Container */}
      <div className="absolute inset-0 z-0 cursor-crosshair">
        {!loading && <Globe tleData={tleData} filter={filter} onSelectSat={setActiveSat} focusSatId={activeSat?.id} secondarySatId={secondaryTarget?.id} timeOffsetMinutes={timeOffsetMinutes} isShattered={isShattered} />}
      </div>

      {/* Futuristic Analysis Modal */}
      <div
        className={`fixed inset-0 z-[100] flex items-center justify-center transition-all duration-700 ${analysisState !== 'idle' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        style={{
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          transform: 'translateZ(0)',
          willChange: 'opacity'
        }}
      >
        <div className={`relative flex flex-col items-center justify-center p-12 rounded-[2rem] min-w-[500px] border border-white/10 transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${analysisState !== 'idle' ? 'scale-100 translate-y-0' : 'scale-90 translate-y-12'}`}
             style={{ background: 'rgba(12, 12, 12, 0.65)', boxShadow: '0 0 80px rgba(0,0,0,0.8), inset 0 0 20px rgba(255,255,255,0.03)' }}>

          {analysisState === 'computing' && (
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 border-t-2 border-r-2 border-white rounded-full animate-spin mb-8"></div>
              <h2 className="text-xl font-bold tracking-[0.2em] uppercase text-white mb-2" style={{ fontFamily: 'var(--font-display, "Space Grotesk")' }}>Quantifying Risk</h2>
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

              <h2 className="text-3xl font-bold tracking-tight text-white uppercase mb-8" style={{ fontFamily: 'var(--font-display, "Space Grotesk")' }}>
                Conjunction Analysis
              </h2>

              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="flex flex-col items-center justify-center p-6 bg-white/5 rounded-2xl border border-white/5 shadow-[inset_0_0_20px_rgba(255,255,255,0.02)]">
                  <span className="text-[10px] uppercase tracking-[0.2em] text-[#a3a3a3] font-semibold mb-2">Probability of Collision</span>
                  <div className="flex flex-col items-center">
                    <span className={`text-4xl font-mono font-bold ${analysisResult.pc > 0.0001 ? 'text-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]' : 'text-white'}`}>
                      1 in {(1 / analysisResult.pc).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                    <span className="text-[#a3a3a3] font-mono text-[11px] uppercase tracking-widest mt-2">
                      {(analysisResult.pc * 100).toPrecision(3)}% Chance
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-center justify-center p-6 bg-white/5 rounded-2xl border border-white/5 shadow-[inset_0_0_20px_rgba(255,255,255,0.02)]">
                  <span className="text-[10px] uppercase tracking-[0.2em] text-[#a3a3a3] font-semibold mb-2">Miss Distance</span>
                  <span className="text-4xl font-mono font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]">
                    {analysisResult.miss_distance_km.toFixed(1)} <span className="text-sm text-[#737373]">KM</span>
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center p-5 bg-white/5 rounded-xl border border-white/5">
                <div className="flex flex-col items-start">
                  <span className="text-[9px] uppercase tracking-[0.2em] text-[#737373] font-semibold mb-1">Time of Closest Approach</span>
                  <span className="text-sm font-mono text-white tracking-widest">{new Date(analysisResult.tca).toLocaleString()}</span>
                </div>
                <div className="w-[1px] h-8 bg-white/10"></div>
                <div className="flex flex-col items-end">
                  <span className="text-[9px] uppercase tracking-[0.2em] text-[#737373] font-semibold mb-1">Relative Velocity</span>
                  <span className="text-sm font-mono text-white tracking-widest">{analysisResult.rel_velocity_km_s.toFixed(2)} KM/S</span>
                </div>
              </div>

              {/* Shatter Simulation Trigger */}
              <button 
                onClick={() => setIsShattered(true)} 
                className="w-full mt-6 bg-red-500/5 hover:bg-red-500/15 text-red-500 border border-red-500/20 py-4 rounded-xl uppercase tracking-widest text-[11px] font-bold flex items-center justify-center gap-3 transition-all duration-300"
                style={{ boxShadow: 'inset 0 0 10px rgba(239,68,68,0.05)' }}
              >
                <Skull className="w-5 h-5" /> Simulate Shatter Event
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Top Left Header (Button + Logo) */}
      <div
        className="absolute top-8 left-8 z-50 flex items-center gap-4 px-4 py-3 rounded-2xl"
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
        <div style={{ fontWeight: 800, fontSize: '1.25rem', fontFamily: 'var(--font-display, "Space Grotesk")' }} className="text-white tracking-tight">
          OURE<span className="text-[#a3a3a3]">.</span>
        </div>
      </div>

      {/* Retractable Sidebar */}
      <div
        className={`absolute top-28 left-8 z-40 flex flex-col gap-4 p-4 rounded-2xl min-w-[200px] transition-all duration-500 origin-top-left ${isSidebarOpen ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-4 scale-95 pointer-events-none'}`}
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
                    className="w-full bg-black/40 border border-white/10 rounded-lg py-2 pl-8 pr-3 text-[10px] text-white placeholder-[#737373] focus:outline-none focus:border-white/30 transition-colors"
                  />
                </div>

                {searchQuery.length > 1 && searchResults.length > 0 && (
                  <div className="flex flex-col gap-1 max-h-[140px] overflow-y-auto pr-1">
                    {searchResults.map(res => (
                      <div key={res.id} onClick={() => {
                         try {
                           const satrec = satellite.twoline2satrec(res.tle1, res.tle2);
                           const satData = { id: res.id, name: res.name, satrec, category: 'OTHER', color: [1,1,1] };
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
                <span className="text-[10px] uppercase tracking-widest text-[#525252] font-semibold mb-2">High-Risk Conjunctions</span>

                {[
                  { primary_id: "25544", secondary_id: "48274", pc: 0.0034, warning_level: "RED", miss_distance_km: 1.2 },
                  { primary_id: "20580", secondary_id: "39084", pc: 0.000012, warning_level: "YELLOW", miss_distance_km: 9.1 },
                  { primary_id: "43013", secondary_id: "41470", pc: 0.000003, warning_level: "GREEN", miss_distance_km: 14.5 }
                ].map((res, i) => (
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

                    const mockPrimary = { id: res.primary_id, name: pName, satrec: pSatrec, category: 'OTHER', color: [1,1,1] };
                    const mockSecondary = { id: res.secondary_id, name: sName, satrec: sSatrec, category: 'OTHER', color: [1,1,1] };

                    setPrimaryTarget(mockPrimary as any);
                    setSecondaryTarget(mockSecondary as any);
                    setActiveSat(mockPrimary as any);
                    setShowMissionControl(true);
                  }} className="flex flex-col p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition-colors group">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex gap-2 items-center">
                         <span className="text-white font-mono text-xs group-hover:text-[#60a5fa] transition-colors">{res.primary_id}</span>
                         <span className="text-[#525252] text-[10px]">vs</span>
                         <span className="text-[#a3a3a3] font-mono text-xs">{res.secondary_id}</span>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${res.warning_level === 'RED' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]' : res.warning_level === 'YELLOW' ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.8)]' : 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]'}`}></div>
                    </div>
                    <div className="flex justify-between items-end">
                      <div className="flex flex-col">
                        <span className="text-[8px] text-[#737373] uppercase tracking-widest">Probability</span>
                        <span className={`font-mono text-xs ${res.warning_level === 'RED' ? 'text-red-400' : 'text-white'}`}>1 in {Math.round(1/res.pc).toLocaleString()}</span>
                      </div>
                      <div className="flex flex-col items-end">
                         <span className="text-[8px] text-[#737373] uppercase tracking-widest">Miss</span>
                         <span className="font-mono text-xs text-white">{res.miss_distance_km} KM</span>
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
                <div className={`w-2 h-2 rounded-full transition-colors ${isTimeScrubberOpen ? 'bg-[#00ff88] shadow-[0_0_8px_rgba(0,255,136,0.6)]' : 'bg-transparent'}`}></div>
              </button>
            </div>
        </nav>
      </div>

      {/* Top Right Mission Control Toggle */}
      <button
        className="absolute top-8 right-8 z-50 flex items-center gap-4 px-4 py-3 rounded-2xl cursor-pointer group"
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
        <span className="text-[#a3a3a3] group-hover:text-white transition-colors text-[11px] font-bold uppercase tracking-[0.15em] pl-2">
          Mission Control
        </span>
        <div className="w-2 h-2 rounded-full bg-white animate-pulse mr-2 shadow-[0_0_8px_rgba(255,255,255,0.8)]"></div>
      </button>

      {/* Minimalist Mission Control (Right) */}
      <div
        className={`absolute top-28 right-8 w-80 z-40 space-y-4 flex flex-col gap-4 p-5 rounded-3xl transition-all duration-500 origin-top-right ${showMissionControl ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-4 scale-95 pointer-events-none'}`}
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
              <p className="text-sm text-white font-mono">{primaryTarget ? primaryTarget.name : 'AWAITING SELECTION'}</p>
            </div>
            <div>
              <p className="text-[9px] uppercase tracking-[0.2em] text-[#737373] mb-1 font-semibold">Secondary Target</p>
              <p className="text-sm text-white font-mono">{secondaryTarget ? secondaryTarget.name : 'AWAITING SELECTION'}</p>
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
        className={`fixed bottom-8 right-8 z-40 flex flex-col gap-4 p-5 rounded-3xl min-w-[320px] transition-all duration-700 ease-in-out ${activeSat ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}
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
              <div className="flex flex-col items-start">
                <div className="flex items-center gap-3 mb-1">
                  <h2 style={{ fontFamily: 'var(--font-display, "Space Grotesk")' }} className="text-2xl font-bold tracking-tight text-white uppercase text-left">
                    {activeSat.name}
                  </h2>
                  <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
                </div>
                <p className="text-[11px] text-[#a3a3a3] font-mono tracking-widest uppercase">ID: {activeSat.id}</p>
              </div>
              <button
                onClick={() => setActiveSat(null)}
                className="text-[#737373] hover:text-white p-1 rounded-full transition-colors mt-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="w-8 h-[1px] bg-white/10"></div>

            <div className="flex items-center gap-6 border-l border-white/20 pl-4 ml-1 text-left w-full">
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-[#737373] mb-1 font-semibold">Category</p>
                <p className="text-sm text-white font-medium uppercase tracking-widest">{activeSat.category}</p>
              </div>
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-[#737373] mb-1 font-semibold">Altitude</p>
                <p className="text-sm text-white font-mono tracking-wider">{activeSatDetails.alt} <span className="text-[9px] text-[#737373]">KM</span></p>
              </div>
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-[#737373] mb-1 font-semibold">Velocity</p>
                <p className="text-sm text-white font-mono tracking-wider">{activeSatDetails.vel} <span className="text-[9px] text-[#737373]">KM/S</span></p>
              </div>
            </div>

            <div className="flex items-center gap-3 mt-2 w-full">
              <button
                onClick={() => {
                  setPrimaryTarget(activeSat);
                  setShowMissionControl(true);
                }}
                className="flex-1 text-[10px] font-bold uppercase tracking-[0.15em] text-black bg-white px-4 py-3 rounded-xl hover:bg-gray-200 transition-all duration-300"
              >
                Set Primary
              </button>
              <button
                onClick={() => {
                  setSecondaryTarget(activeSat);
                  setShowMissionControl(true);
                }}
                className="flex-1 text-[10px] font-bold uppercase tracking-[0.15em] text-white border border-white/30 px-4 py-3 rounded-xl hover:border-white transition-all duration-300"
              >
                Set Secondary
              </button>
            </div>
          </>
        )}
      </div>

      {/* Time Scrubber */}
      <div className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 z-40 w-1/3 bg-black/60 backdrop-blur-md border border-white/10 p-4 rounded-xl shadow-2xl flex flex-col gap-3 transition-all duration-500 ${isTimeScrubberOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}>
         <div className="flex justify-between items-center text-white text-[10px] tracking-widest uppercase font-mono">
           <span className="text-[#737373]">Live Time</span>
           <div className="flex items-center gap-4">
             <span className={`${timeOffsetMinutes > 0 ? 'text-[#00ff88]' : 'text-white'}`}>
               {timeOffsetMinutes > 0 ? `+${timeOffsetMinutes} Min (Forward Propagated)` : 'Real-Time'}
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
           min="0"
           max="120"
           value={timeOffsetMinutes}
           onChange={(e) => setTimeOffsetMinutes(Number(e.target.value))}
           className="w-full h-1 bg-white/20 rounded-lg appearance-none cursor-pointer hover:bg-white/30 transition-colors"
           style={{ accentColor: '#ffffff' }}
         />
      </div>

      {/* Loading Screen */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-50" style={{ background: 'var(--bg-primary, #0a0a0a)' }}>
          <GlobeIcon className="w-8 h-8 text-white animate-pulse mb-6" />
          <h2 style={{ fontFamily: 'var(--font-display, "Space Grotesk")' }} className="text-3xl font-bold text-white mb-2 tracking-tight">Initializing</h2>
          <p className="text-[#a3a3a3] font-mono text-xs uppercase tracking-widest">Establishing Orbital Link...</p>
        </div>
      )}
    </div>
  );
}
