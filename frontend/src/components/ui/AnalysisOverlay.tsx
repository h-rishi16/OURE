import React from 'react';
import { Target, X } from 'lucide-react';
import { formatProbability } from '@/lib/utils';

export interface AnalysisOverlayProps {
  primaryTarget: any;
  secondaryTarget: any;
  analysisState: 'idle' | 'computing' | 'complete';
  analysisResult: any;
  avoidState: 'idle' | 'computing' | 'complete';
  avoidResult: any;
  onClose: () => void;
}

export const AnalysisOverlay: React.FC<AnalysisOverlayProps> = ({
  primaryTarget,
  secondaryTarget,
  analysisState,
  analysisResult,
  avoidState,
  avoidResult,
  onClose
}) => {
  return (
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
            <button className="absolute top-6 right-6 text-[#737373] hover:text-white transition-colors p-2 cursor-pointer" onClick={onClose}>
              <X className="w-6 h-6" />
            </button>

            <h2 className="text-3xl font-bold tracking-tight text-white uppercase mb-4 font-display">
              Conjunction Analysis
            </h2>

            <div className="flex flex-col items-center gap-2 mb-10">
              <span className="text-sm font-mono text-neutral-400">
                <span className="text-white">{primaryTarget?.name || primaryTarget?.id}</span> vs <span className="text-white">{secondaryTarget?.name || secondaryTarget?.id}</span>
              </span>
            </div>

            <div className="flex flex-col gap-8 mb-8 text-left w-full px-4">
              <div>
                <span className="text-xs uppercase tracking-widest text-neutral-500 font-medium mb-1 block">Probability of Collision</span>
                <div className="flex items-baseline gap-4">
                  <span className={`text-6xl font-light font-display tracking-tight ${
                    analysisResult.warning_level === 'RED' ? 'text-red-500' : 'text-white'
                  }`}>
                    {formatProbability(analysisResult.pc)}
                  </span>
                  <span className="text-neutral-500 font-mono text-sm uppercase tracking-widest">
                    {(analysisResult.pc * 100).toPrecision(3)}%
                  </span>
                </div>
              </div>

              <div className="flex flex-row items-center justify-between border-t border-white/10 pt-6">
                <div>
                  <span className="text-xs uppercase tracking-widest text-neutral-500 font-medium mb-1 block">Miss Distance</span>
                  <span className="text-2xl font-light font-display text-white tracking-tight">
                    {analysisResult.miss_distance_km.toFixed(1)} <span className="text-sm font-sans text-neutral-500">km</span>
                  </span>
                </div>
                <div>
                  <span className="text-xs uppercase tracking-widest text-neutral-500 font-medium mb-1 block">Relative Velocity</span>
                  <span className="text-2xl font-light font-display text-white tracking-tight">
                    {analysisResult.rel_velocity_km_s.toFixed(2)} <span className="text-sm font-sans text-neutral-500">km/s</span>
                  </span>
                </div>
              </div>

              <div className="border-t border-white/10 pt-6">
                <span className="text-xs uppercase tracking-widest text-neutral-500 font-medium mb-1 block">Time of Closest Approach</span>
                <span className="text-lg font-mono text-neutral-300 tracking-wider">
                  {new Date(analysisResult.tca).toUTCString()}
                </span>
              </div>
            </div>



          </div>
        )}
      </div>
    </div>
  );
};
