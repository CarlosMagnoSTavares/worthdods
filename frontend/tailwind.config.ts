import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        serif: ["DM Serif Display", "serif"],
      },
      colors: {
        ink: "#0d1117",
        paper: "#f5f0e8",
        cream: "#ede8dc",
        gold: "#b8860b",
        "gold-light": "#d4a017",
        "gold-pale": "#f5e6b0",
        mid: "#6b6055",
        border: "#d0c8b8",
      },
    },
  },
  plugins: [],
};

export default config;
