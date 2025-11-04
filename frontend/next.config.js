/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  basePath: process.env.NODE_ENV === 'production' ? '/1' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/1/' : '',
}

module.exports = nextConfig
