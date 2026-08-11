import * as THREE from 'three';

export function getCountryBorders(geojson: any, radius: number): Float32Array {
  const vertices: number[] = [];

  const addLine = (ring: number[][]) => {
    for (let i = 0; i < ring.length - 1; i++) {
      const p1 = ring[i];
      const p2 = ring[i + 1];

      for (const [lon, lat] of [p1, p2]) {
        const latRad = lat * (Math.PI / 180);
        const lonRad = lon * (Math.PI / 180);

        const x = radius * Math.cos(latRad) * Math.cos(lonRad);
        const y = radius * Math.sin(latRad);
        const z = -radius * Math.cos(latRad) * Math.sin(lonRad);

        vertices.push(x, y, z);
      }
    }
  };

  for (const feature of geojson.features) {
    if (!feature.geometry) continue;

    if (feature.geometry.type === 'Polygon') {
      for (const ring of feature.geometry.coordinates) {
        addLine(ring);
      }
    } else if (feature.geometry.type === 'MultiPolygon') {
      for (const polygon of feature.geometry.coordinates) {
        for (const ring of polygon) {
          addLine(ring);
        }
      }
    }
  }

  return new Float32Array(vertices);
}
