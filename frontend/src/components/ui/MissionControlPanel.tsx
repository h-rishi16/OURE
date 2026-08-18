import React from 'react';
import { X } from 'lucide-react';
import { SatelliteData } from '../Globe';

interface MissionControlPanelProps {
  showMissionControl: boolean;
  setShowMissionControl: (v: boolean) => void;
  setActiveSat: (sat: SatelliteData | null) => void;
  primaryTarget: SatelliteData | null;
  setPrimaryTarget: (sat: SatelliteData | null) => void;
  secondaryTarget: SatelliteData | null;
  setSecondaryTarget: (sat: SatelliteData | null) => void;
  setEscapeTrajectory: (traj: number[][] | null) => void;
  handleRunAnalysis: () => void;
}

export const MissionControlPanel: React.FC<MissionControlPanelProps> = ({
  showMissionControl,
  setShowMissionControl,
  setActiveSat,
  primaryTarget,
  setPrimaryTarget,
  secondaryTarget,
  setSecondaryTarget,
  setEscapeTrajectory,
  handleRunAnalysis
}) => {
  return (
    <div
      className={`absolute top-20 lg:top-28 right-4 left-4 md:left-auto md:right-8 w-auto md:w-80 z-40 space-y-4 flex flex-col gap-4 p-5 rounded-3xl max-h-[calc(100dvh-6rem)] overflow-y-auto transition-all duration-500 origin-top-right ${showMissionControl ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-4 scale-95 pointer-events-none'}`}
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
        <button onClick={() => { setShowMissionControl(false); setActiveSat(null); setPrimaryTarget(null); setSecondaryTarget(null); setEscapeTrajectory(null); }} className="text-[#737373] hover:text-white p-1 rounded-full transition-colors">
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
  );
};
