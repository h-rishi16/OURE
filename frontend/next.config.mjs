/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/tles',
        destination: 'http://127.0.0.1:8000/ui/api/tles',
      },
      {
        source: '/ui/analyze',
        destination: 'http://127.0.0.1:8000/ui/analyze',
      }
    ]
  },
};

export default nextConfig;
