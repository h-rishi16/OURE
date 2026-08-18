import React from 'react';

export const PixelAstronaut = () => {
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
