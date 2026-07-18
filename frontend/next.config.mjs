/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/tles',
        // Assuming the python backend runs on 8000 by default, or we can fetch from an actual url
        // We'll point to Celestrak as a fallback for the frontend to work standalone
        destination: 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',
      },
    ]
  },
};

export default nextConfig;
