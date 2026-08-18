export const FILTERS = [
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
