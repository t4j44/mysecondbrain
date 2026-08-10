/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#12081d",
          fg: "#f7f4ea",
          panel: "#0a0510",
          accent: "#00ff9d",
          accentHover: "#00e68e",
          border: "rgba(247, 244, 234, 0.12)",
          muted: "rgba(247, 244, 234, 0.5)",
          alert: "#ff3e3e",
          warn: "#ffb63e",
        }
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      borderWidth: {
        1: "1px",
      }
    },
  },
  plugins: [],
}
