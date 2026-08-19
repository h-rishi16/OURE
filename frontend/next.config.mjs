/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
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
