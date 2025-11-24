/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "ae-ink": "#0f172a",
        "ae-pearl": "#f8fafc",
        "ae-glow": "#dbeafe",
      },
      fontFamily: {
        sans: [
          "SF Pro Display",
          "SF Pro Text",
          "-apple-system",
          "BlinkMacSystemFont",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        glass: "0 20px 60px -25px rgba(15, 23, 42, 0.35)",
      },
      backgroundImage: {
        "ae-gradient":
          "radial-gradient(circle at top, rgba(59, 130, 246, 0.16), transparent 55%), radial-gradient(circle at bottom, rgba(236, 72, 153, 0.18), transparent 60%)",
      },
    },
  },
  plugins: [],
};
