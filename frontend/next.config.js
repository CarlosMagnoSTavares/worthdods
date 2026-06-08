/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "venda-imoveis.caixa.gov.br",
      },
    ],
  },
};

module.exports = nextConfig;
