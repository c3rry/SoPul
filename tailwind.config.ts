import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        dem: {
          light: "#93c5fd",
          DEFAULT: "#2563eb",
          dark: "#1d4ed8",
          deep: "#1e3a8a",
        },
        rep: {
          light: "#fca5a5",
          DEFAULT: "#dc2626",
          dark: "#b91c1c",
          deep: "#7f1d1d",
        },
        tossup: {
          light: "#fef08a",
          DEFAULT: "#eab308",
          dark: "#ca8a04",
        },
        surface: {
          50: "#090d16",
          100: "#0f172a",
          200: "#1e293b",
          300: "#334155",
          400: "#475569",
        },
      },
      fontFamily: {
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
