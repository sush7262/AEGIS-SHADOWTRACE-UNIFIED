/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        display: ["Orbitron", "system-ui", "sans-serif"],
      },
      colors: {
        cyber: {
          bg: "#070b12",
          panel: "#0d1424",
          border: "#1e2a45",
          accent: "#00f0ff",
          danger: "#ff3366",
          warn: "#ffaa00",
          muted: "#6b7a99",
          glow: "#00f0ff33",
        },
      },
      boxShadow: {
        glow: "0 0 24px rgba(0, 240, 255, 0.15)",
        card: "0 4px 32px rgba(0, 0, 0, 0.45)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(30, 42, 69, 0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(30, 42, 69, 0.35) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "48px 48px",
      },
    },
  },
  plugins: [],
};
