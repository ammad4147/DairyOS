import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Pinned dev-server port (2026-08-14): no vite.config.ts existed before
// this, so Vite silently auto-incremented past 5173 whenever a stale
// process was still holding it -- which is exactly what caused the
// dashboard to 404 against itself (the frontend's own CORS/API-host
// detection only recognized a range of ports, and Vite had drifted past
// it). `strictPort: true` makes that failure loud and immediate instead
// of a silent drift; the one-click launcher (scripts/start_dairyos.ps1)
// frees this port before every launch so the failure shouldn't be seen
// in normal use.
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        strictPort: true,
    },
});
