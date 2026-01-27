/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable server actions
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

export default nextConfig;
