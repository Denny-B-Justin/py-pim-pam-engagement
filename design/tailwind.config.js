/**
 * Tailwind 3.4 configuration — identical palette / fonts to the original Next.js site.
 *
 * The compiled output (../assets/00-tailwind.css) is committed, so Posit Connect and local runs
 * need no Node. Rebuild only after adding NEW utility classes to the Python files:
 *
 *     cd design && npm install && npm run build
 */
const path = require("path");
const root = path.join(__dirname, "..");

module.exports = {
  // Tailwind only emits classes it finds as complete strings in these files.
  content: [
    path.join(root, "*.py"),
    path.join(root, "pages", "*.py"),
    path.join(root, "utils", "*.py"),
    path.join(root, "services", "*.py"),
    path.join(root, "assets", "*.js"),
  ],
  theme: {
    extend: {
      colors: {
        // PIM-PAM brand palette (per branding guidelines)
        brand: {
          blue: "#374291",   // Dark Blue — headings (light bg), links, buttons
          mid: "#3675b7",    // Mid Blue — secondary headings, accents, header/footer bg
          navy: "#021420",   // Azure — darkest text, dark backgrounds, button hover
          light: "#64cbd6",  // Light Blue
          purple: "#4345aa", // Purple — AI, alternate buttons
          orange: "#f26b23", // Orange
          green: "#37b37f",  // Green
          line: "#c9d3ea",  // borders / muted links on dark
          tint: "#dee5f5",   // table header / light fill
        },
        // Engagement scale — data encoding, kept stable (matches map + country page)
        scale: {
          inception: "#FCE5A2",
          awareness: "#F6B26B",
          application: "#3D85C6",
          adoption: "#1F4E79",
        },
        ink: "#1f2d3d",
      },
      fontFamily: {
        // Inter for body, Fira Sans for headings (self-hosted, see assets/style.css)
        sans: ["var(--font-inter)", "Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        heading: ["var(--font-fira)", "Fira Sans", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
