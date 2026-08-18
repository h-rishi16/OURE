import React from 'react';
import { Search, Clock } from 'lucide-react';
import { formatProbability } from '@/lib/utils';
import * as satellite from 'satellite.js';

interface SidebarPanelProps {
  isOpen: boolean;
  view: 'catalog' | 'analysis';
  setView: (view: 'catalog' | 'analysis') => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  searchResults: any[];
  filter: string;
  setFilter: (f: string) => void;
  filtersList: { id: string; label: string }[];
  onSelectCatalogItem: (res: any) => void;
  mockConjunctions: any[];
  onRefreshConjunctions: () => void;
  onSelectConjunction: (res: any) => void;
  isTimeScrubberOpen: boolean;
  setIsTimeScrubberOpen: (open: boolean) => void;
}

export const SidebarPanel: React.FC<SidebarPanelProps> = ({
  isOpen,
  view,
  setView,
  searchQuery,
  setSearchQuery,
  searchResults,
  filter,
  setFilter,
  filtersList,
  onSelectCatalogItem,
  mockConjunctions,
  onRefreshConjunctions,
  onSelectConjunction,
  isTimeScrubberOpen,
  setIsTimeScrubberOpen,
}) => {
  return (
    <div
      className={`absolute top-20 md:top-28 left-4 right-4 md:right-auto md:left-8 z-40 flex flex-col gap-4 p-4 rounded-2xl md:min-w-[300px] max-h-[75vh] overflow-y-auto transition-all duration-500 origin-top-left ${isOpen ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-4 scale-95 pointer-events-none'}`}
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
            onClick={() => setView('catalog')}
            className={`transition-all duration-300 text-xs font-semibold tracking-[0.1em] uppercase relative pb-3 border-b-2 ${view === 'catalog' ? 'text-white border-white' : 'text-[#a3a3a3] border-transparent hover:text-white'}`}
          >
            Catalog
          </button>
          <button
            onClick={() => setView('analysis')}
            className={`transition-all duration-300 text-xs font-semibold tracking-[0.1em] uppercase relative pb-3 border-b-2 ${view === 'analysis' ? 'text-white border-white' : 'text-[#a3a3a3] border-transparent hover:text-white'}`}
          >
            Analysis
          </button>
        </div>

        {view === 'catalog' && (
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
                  <div key={res.id} onClick={() => onSelectCatalogItem(res)} className="text-[10px] text-[#a3a3a3] hover:text-white cursor-pointer py-1.5 px-2 hover:bg-white/10 rounded border border-transparent hover:border-white/5 transition-all flex justify-between items-center group">
                     <span className="truncate max-w-[120px] font-medium group-hover:text-white transition-colors">{res.name}</span>
                     <span className="font-mono text-[9px] text-[#525252] group-hover:text-[#a3a3a3] transition-colors">{res.id}</span>
                  </div>
                ))}
              </div>
            )}

            {(searchQuery.length > 1 && searchResults.length > 0) && <div className="w-full h-[1px] bg-white/5"></div>}

            <span className="text-[10px] uppercase tracking-widest text-[#525252] font-semibold mb-1">Filters</span>
            {filtersList.map(f => (
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

        {view === 'analysis' && (
          <div className="flex flex-col gap-3 w-full">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] uppercase tracking-widest text-[#525252] font-semibold">High-Risk Conjunctions</span>
              <button onClick={onRefreshConjunctions} className="text-[9px] uppercase tracking-widest text-[#a3a3a3] hover:text-white transition-colors bg-white/5 hover:bg-white/10 px-2 py-1 rounded">
                Refresh
              </button>
            </div>

            {mockConjunctions.map((res, i) => (
              <div key={i} onClick={() => onSelectConjunction(res)} className="flex flex-col p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition-colors group">
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
  );
};
