/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Ops Center Command Console Tokens
        ops: {
          base: "#0B0F17",
          panel: "#131A26",
          border: "#232C3D",
          text: "#E7ECF3",
          muted: "#8B95A7",
          live: "#3DA9FC",
          ok: "#34C77B",
          warning: "#E8A33D",
          critical: "#E5484D"
        },
        // Student Self-Service App Tokens
        student: {
          bg: "#FAFAF8",
          panel: "#FFFFFF",
          border: "#E2E8F0",
          text: "#0F172A",
          muted: "#64748B",
          accent: "#0D9488",
          accentHover: "#0F766E"
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace']
      }
    },
  },
  plugins: [],
}
