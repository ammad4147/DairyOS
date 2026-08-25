import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Pinned dev-server port (2026-08-14): no vite.config.ts existed before
// this, so Vite silently auto-incremented past 5173 whenever a stale
// process was still holding it -- which is exactly what caused the
// dashboard to 404 against itself. strictPort makes that failure loud
// and immediate instead of a silent drift.
export default defineConfig({
    base: './',
    plugins: [react()],
    server: {
        port: 5173,
        strictPort: true,
    },
});


