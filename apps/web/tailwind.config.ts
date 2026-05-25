import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#171428",
        panel: "#211F35",
        panel2: "#2B2942",
        line: "rgba(255,255,255,.10)",
        text: "#F4F6FB",
        muted: "#9FA5B8",
        cyan: "#4DA3FF",
        lime: "#32D583",
        amber: "#F7B955",
        rose: "#F97066"
      },
      boxShadow: {
        glow: "0 24px 70px rgba(3, 2, 18, .36)"
      }
    }
  },
  plugins: []
};

export default config;
