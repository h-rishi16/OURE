/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://92.4.73.195/api/:path*', // Proxy to Oracle server Python Backend
      },
    ];
  }
};

export default nextConfig;
