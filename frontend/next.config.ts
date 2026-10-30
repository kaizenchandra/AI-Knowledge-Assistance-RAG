import type { NextConfig } from "next";
const config: NextConfig = {
  output: "standalone",
  experimental: { proxyClientMaxBodySize: "21mb" },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination:
          (process.env.API_INTERNAL_URL || "http://api:8000") + "/api/:path*",
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "same-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};
export default config;
