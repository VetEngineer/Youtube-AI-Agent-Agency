import path from "path";
import type { NextConfig } from "next";

const repoRoot = path.resolve(__dirname, "../..");

const API_INTERNAL_URL = process.env.API_INTERNAL_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  output: 'standalone',
  outputFileTracingRoot: repoRoot,
  turbopack: {
    root: repoRoot,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  rewrites: async () => [
    {
      source: '/api/v1/:path*',
      destination: `${API_INTERNAL_URL}/api/v1/:path*`,
    },
  ],
};

export default nextConfig;
