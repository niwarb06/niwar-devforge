/** @type {import('next').NextConfig} */
const nextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  transpilePackages: [
    "@niwar-devforge/web-bff-core",
    "@niwar-devforge/web-session-core",
  ],
};

export default nextConfig;
