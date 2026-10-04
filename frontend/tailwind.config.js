/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080b10",
        surface: "#0f141e",
        "surface-raised": "#151c2a",
        "surface-card": "#101623",
        border: "#1e293b",
        "border-subtle": "#162032",
        "text-primary": "#f8fafc",
        "text-secondary": "#94a3b8",
        "text-muted": "#64748b",
        trade: {
          buy: "#10b981",
          "buy-glow": "rgba(16, 185, 129, 0.15)",
          sell: "#f43f5e",
          "sell-glow": "rgba(244, 63, 94, 0.15)",
          hold: "#f59e0b",
          "hold-glow": "rgba(245, 158, 11, 0.15)",
          abstain: "#64748b",
          "abstain-glow": "rgba(100, 116, 139, 0.15)",
        },
        intel: {
          blue: "#38bdf8",
          indigo: "#6366f1",
          purple: "#a855f7",
          cyan: "#06b6d4",
        },
        guardian: {
          approve: "#10b981",
          reduce: "#f59e0b",
          reject: "#ef4444",
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "SF Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};
