import React from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { PixelAstronaut } from './PixelAstronaut';

interface AlertHUDProps {
  activeSat: any;
  activeSatDetails: { alt: string; vel: string };
  setActiveSat: (sat: any) => void;
  primaryTarget: any;
  setPrimaryTarget: (sat: any) => void;
  secondaryTarget: any;
  setSecondaryTarget: (sat: any) => void;
  setShowMissionControl: (show: boolean) => void;
}

export const AlertHUD: React.FC<AlertHUDProps> = ({
  activeSat,
  activeSatDetails,
  setActiveSat,
  primaryTarget,
  setPrimaryTarget,
  secondaryTarget,
  setSecondaryTarget,
  setShowMissionControl
}) => {
  if (!activeSat) return null;

  return (
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
  );
};
