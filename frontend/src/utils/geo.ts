import * as THREE from 'three';

export function getCountryBorders(geojson: any, radius: number): THREE.Vector3[][] {
  const lines: THREE.Vector3[][] = [];

  const addLine = (ring: number[][]) => {
    const points: THREE.Vector3[] = [];
    for (const [lon, lat] of ring) {
      const latRad = lat * (Math.PI / 180);
      const lonRad = lon * (Math.PI / 180);

      // ECEF to Three.js right-handed mapping
      // Three.x = ECEF.y (Lon 90 East goes to Right)
      // Three.y = ECEF.z (North Pole goes Up)
      // Three.z = ECEF.x (Lon 0 goes to Front)
      const x = radius * Math.cos(latRad) * Math.sin(lonRad);
      const y = radius * Math.sin(latRad);
      const z = radius * Math.cos(latRad) * Math.cos(lonRad);

      points.push(new THREE.Vector3(x, y, z));
    }
    lines.push(points);
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

  return lines;
}
