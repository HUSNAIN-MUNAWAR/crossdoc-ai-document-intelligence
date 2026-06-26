import type { Config } from "tailwindcss";
const config: Config = { content:["./app/**/*.{ts,tsx}","./components/**/*.{ts,tsx}"], darkMode:"class", theme:{extend:{boxShadow:{soft:"0 20px 45px rgba(15,23,42,.18)"}}}, plugins:[] };
export default config;
