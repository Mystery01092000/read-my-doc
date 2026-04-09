import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#000000",
        surface: "#131313",
        "surface-container-lowest": "#0f0f0f",
        "surface-container-low": "#1b1b1b",
        "surface-container-high": "#2a2a2a",
        "surface-container-highest": "#353535",
        "on-surface": "#e2e2e2",
        "on-surface-variant": "#c2c6d6",
        primary: "#adc6ff",
        "primary-container": "#4d8eff",
        secondary: "#b1c6f9",
        "outline-variant": "#424754",
        outline: "#8c909f",
      },
      borderRadius: {
        xl: "1.5rem",
      },
      fontFamily: {
        headline: ["Plus Jakarta Sans"],
        body: ["Manrope"],
        label: ["Manrope"],
      },
      backdropBlur: {
        "32": "32px",
      },
    },
  },
  plugins: [],
};

export default config;
