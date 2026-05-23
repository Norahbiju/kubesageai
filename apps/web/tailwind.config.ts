import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#080A0F",
        panel: "#0D111A",
        panel2: "#111722",
        line: "#222A38",
        text: "#E7ECF4",
        muted: "#8D99AA",
        cyan: "#5CE1E6",
        lime: "#B7F566",
        amber: "#FFCD70",
        rose: "#FF6B8A"
      },
      boxShadow: {
        glow: "0 0 60px rgba(92, 225, 230, .14)"
      }
    }
  },
  plugins: []
};

export default config;
