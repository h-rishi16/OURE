'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { SatelliteData } from '../components/Globe';
import { Rocket, Target, Zap, X, Globe as GlobeIcon } from 'lucide-react';
import * as satellite from 'satellite.js';

// Dynamically import Globe to avoid SSR issues with Three.js
const Globe = dynamic(() => import('../components/Globe'), { ssr: false });

const FILTERS = [
  { id: 'ALL', label: 'All' },
  { id: 'STATION', label: 'Stations' },
  { id: 'STARLINK', label: 'Starlink' },
  { id: 'ONEWEB', label: 'OneWeb' },
  { id: 'WEATHER', label: 'Earth Obs' },
  { id: 'NAV', label: 'Navigation' }
];

export default function Home() {
  const [tleData, setTleData] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');

  const [activeSat, setActiveSat] = useState<SatelliteData | null>(null);
  const [primaryTarget, setPrimaryTarget] = useState<SatelliteData | null>(null);
  const [secondaryTarget, setSecondaryTarget] = useState<SatelliteData | null>(null);

  const [activeSatDetails, setActiveSatDetails] = useState({ alt: '0', vel: '0' });

  useEffect(() => {
    // Fetch TLE data. We'll set up a rewrite in next.config.js to point /api to the Python backend
    fetch('/api/tles')
      .then(res => res.text())
      .then(data => {
        const lines = data.split('\n').map(l => l.trim()).filter(l => l.length > 0);
        setTleData(lines);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching TLEs:", err);
        setLoading(false); // Handle error visually if needed
      });
  }, []);

  // Update alt/vel when active sat changes
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

  const getVisibleCount = () => {
    if (tleData.length === 0) return 0;
    // Count satellites roughly based on lines (3 lines per sat: name, tle1, tle2)
    // For a more accurate count, we'd process all TLEs here too, but this is an approximation for UI speed
    let count = 0;
    // We already parsed this in Globe, but we need it here for the UI.
    // In a real app we might lift state up. For now, estimate based on filter.
    if (filter === 'ALL') return Math.floor(tleData.length / 3);

    // Detailed count if filtered
    for (let i = 0; i < tleData.length; i++) {
        if (tleData[i].startsWith('1 ') && i > 0 && i + 1 < tleData.length) {
            const name = tleData[i - 1];
            if (filter === 'STATION' && (name.includes("ISS") || name.includes("ZARYA") || name.includes("CSS") || name.includes("TIANGONG"))) count++;
            else if (filter === 'STARLINK' && name.includes("STARLINK")) count++;
            else if (filter === 'ONEWEB' && name.includes("ONEWEB")) count++;
            else if (filter === 'WEATHER' && (name.includes("NOAA") || name.includes("GOES") || name.includes("METEOR") || name.includes("TERRA") || name.includes("AQUA") || name.includes("FLOCK") || name.includes("LANDSAT"))) count++;
            else if (filter === 'NAV' && (name.includes("NAVSTAR") || name.includes("GLONASS") || name.includes("GALILEO") || name.includes("BEIDOU") || name.includes("GPS") || name.includes("QZS"))) count++;
        }
    }
    return count;
  };

  const handleRunAnalysis = () => {
    if (primaryTarget && secondaryTarget) {
      window.location.href = `/ui/?primary=${primaryTarget.id}&secondary=${secondaryTarget.id}`;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#a3a3a3] font-sans relative overflow-hidden space-time-grid">

      {/* 3D Globe Container */}
      <div className="absolute inset-0 z-0">
        {!loading && <Globe tleData={tleData} filter={filter} onSelectSat={setActiveSat} />}
      </div>

      {/* Cinematic Header Overlay */}
      <div className="absolute top-6 left-1/2 transform -translate-x-1/2 z-10 text-center pointer-events-none">
        <h1 className="font-display text-4xl font-bold tracking-tight text-silver-gradient drop-shadow-lg">
          OURE SSA
        </h1>
        <p className="text-sm font-medium tracking-widest uppercase opacity-70 mt-1">Orbital Uncertainty & Risk Engine</p>
      </div>

      {/* Category Filter Pills (Bottom Center) */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex space-x-3 bg-[#0a0a0a]/80 backdrop-blur-md p-2.5 rounded-full border border-[#262626] shadow-2xl z-20">
        {FILTERS.map(f => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-300 ${
              filter === f.id
                ? 'bg-[#ffffff] text-[#0a0a0a] shadow-[0_0_15px_rgba(255,255,255,0.3)]'
                : 'text-[#a3a3a3] hover:text-white hover:bg-[#262626]/50'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Mission Control (Top Right) */}
      <div className="absolute top-6 right-6 bg-[#0a0a0a]/90 backdrop-blur-xl border border-[#262626] rounded-2xl p-6 shadow-2xl w-80 z-20">
        <h3 className="font-display text-xl font-bold text-white mb-5 flex items-center">
          <Rocket className="mr-3 w-5 h-5 text-gray-400" />
          Mission Control
        </h3>

        <div className="mb-4">
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Primary Target</label>
          <div className={`border rounded-xl px-4 py-3 text-sm font-mono truncate transition-colors ${primaryTarget ? 'bg-[#1a1a1a] border-white text-white' : 'bg-[#0f0f0f] border-[#262626] text-gray-600'}`}>
            {primaryTarget ? `[${primaryTarget.id}] ${primaryTarget.name}` : 'None Selected'}
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Secondary Target</label>
          <div className={`border rounded-xl px-4 py-3 text-sm font-mono truncate transition-colors ${secondaryTarget ? 'bg-[#1a1a1a] border-gray-400 text-gray-300' : 'bg-[#0f0f0f] border-[#262626] text-gray-600'}`}>
            {secondaryTarget ? `[${secondaryTarget.id}] ${secondaryTarget.name}` : 'None Selected'}
          </div>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={!primaryTarget || !secondaryTarget}
          className={`w-full font-bold py-3.5 px-4 rounded-xl transition-all duration-300 text-sm flex items-center justify-center ${
            primaryTarget && secondaryTarget
              ? 'bg-white text-[#0a0a0a] hover:bg-gray-200 shadow-[0_0_20px_rgba(255,255,255,0.2)] active:scale-95'
              : 'bg-[#1a1a1a] text-gray-600 border border-[#262626] cursor-not-allowed'
          }`}
        >
          <Zap className="mr-2 w-4 h-4" />
          Run Conjunction Analysis
        </button>
      </div>

      {/* Satellite Info Overlay (Left) */}
      <div className={`absolute top-6 left-6 bg-[#0a0a0a]/90 backdrop-blur-xl border border-[#262626] rounded-2xl p-6 shadow-2xl max-w-sm w-full z-20 transform transition-all duration-300 origin-top-left ${activeSat ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none'}`}>
        {activeSat && (
          <>
            <div className="flex justify-between items-start mb-4">
              <h3 className="font-display text-xl font-bold text-white leading-tight pr-4">
                {activeSat.name}
              </h3>
              <button onClick={() => setActiveSat(null)} className="text-gray-500 hover:text-white transition-colors bg-[#1a1a1a] rounded-full p-1 border border-[#262626]">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 mb-6 bg-[#0f0f0f] p-4 rounded-xl border border-[#262626]">
              <div className="flex justify-between items-center pb-2 border-b border-[#262626]">
                <span className="text-xs font-semibold text-gray-500 uppercase">NORAD ID</span>
                <span className="text-white font-mono font-bold tracking-wider">{activeSat.id}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[#262626]">
                <span className="text-xs font-semibold text-gray-500 uppercase">Category</span>
                <span className="text-white text-xs font-bold px-2.5 py-1 rounded-md bg-[#1a1a1a] border border-[#333]">{activeSat.category}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-[#262626]">
                <span className="text-xs font-semibold text-gray-500 uppercase">Altitude</span>
                <span className="text-gray-300 font-mono"><span className="text-white">{activeSatDetails.alt}</span> km</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-gray-500 uppercase">Velocity</span>
                <span className="text-gray-300 font-mono"><span className="text-white">{activeSatDetails.vel}</span> km/s</span>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => setPrimaryTarget(activeSat)}
                className="flex-1 bg-[#1a1a1a] hover:bg-white hover:text-[#0a0a0a] text-white border border-[#333] font-semibold py-2.5 px-3 rounded-xl transition-all duration-300 text-sm shadow-lg active:scale-95 flex justify-center items-center"
              >
                <Target className="w-4 h-4 mr-2 opacity-70" />
                Set Primary
              </button>
              <button
                onClick={() => setSecondaryTarget(activeSat)}
                className="flex-1 bg-[#0a0a0a] hover:bg-[#1a1a1a] text-gray-300 border border-[#262626] hover:border-gray-500 font-semibold py-2.5 px-3 rounded-xl transition-all duration-300 text-sm shadow-lg active:scale-95"
              >
                Set Secondary
              </button>
            </div>
          </>
        )}
      </div>

      {/* Active Count Stats */}
      <div className="absolute bottom-8 left-8 flex items-center space-x-4 z-20">
        <div className="bg-[#0a0a0a]/80 backdrop-blur-md px-4 py-2.5 rounded-xl border border-[#262626] flex items-center shadow-lg">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse mr-3"></div>
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Live Catalog</span>
            <span className="text-white font-mono text-sm leading-none">{getVisibleCount().toLocaleString()} <span className="text-gray-500">objects</span></span>
          </div>
        </div>
      </div>

      {/* Loading Screen */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0a0a0a] z-50">
          <div className="relative w-24 h-24 mb-8">
            <div className="absolute inset-0 border-2 border-[#262626] rounded-full"></div>
            <div className="absolute inset-0 border-2 border-white rounded-full border-t-transparent animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center text-gray-500">
              <GlobeIcon className="w-8 h-8 animate-pulse" />
            </div>
          </div>
          <h2 className="font-display text-2xl font-bold text-white mb-3 tracking-wide">Initializing SSA Engine</h2>
          <p className="text-gray-500 font-mono text-sm uppercase tracking-widest">Acquiring Telemetry Data...</p>
        </div>
      )}

    </div>
  );
}
