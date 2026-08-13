/**
 * The single source of the DairyOS API base URL.
 *
 * Before this module the host was written out literally in eight files, which
 * made two things impossible: packaging the application (the sidecar backend
 * does not always sit on port 8000) and using DairyOS from a phone (the farm
 * PC is not `localhost` to anything but itself).
 *
 * Resolution order, first match wins:
 *
 *   1. `window.__DAIRYOS_API_URL__` — runtime override. This exists because a
 *      build-time constant cannot know a farm's LAN address, and we ship one
 *      build to every farm. The desktop shell and the LAN/PWA entry point set
 *      it before the app mounts.
 *   2. `VITE_DAIRYOS_API_URL` — build-time, for a deployment pinned at build.
 *   3. The page's own origin, when the page was served over http(s) from
 *      something other than a dev server. In the packaged app and over the LAN
 *      the API and the UI share an origin, so this is the common case and
 *      needs no configuration at all.
 *   4. `http://127.0.0.1:8000` — the development fallback, where Vite serves
 *      the UI on its own port and the backend runs separately.
 */

declare global {
    interface Window {
        __DAIRYOS_API_URL__?: string;
    }
}

/** Ports a Vite dev/preview server occupies; never the API. */
const DEV_SERVER_PORTS = new Set(["5173", "4173"]);

const DEVELOPMENT_FALLBACK = "http://127.0.0.1:8000";

function normalise(value: unknown): string | null {
    if (typeof value !== "string") {
        return null;
    }

    const trimmed = value.trim().replace(/\/+$/, "");

    return trimmed.length > 0 ? trimmed : null;
}

function fromRuntimeOverride(): string | null {
    if (typeof window === "undefined") {
        return null;
    }

    return normalise(window.__DAIRYOS_API_URL__);
}

function fromBuildConfig(): string | null {
    return normalise(import.meta.env?.VITE_DAIRYOS_API_URL);
}

function fromPageOrigin(): string | null {
    if (typeof window === "undefined" || !window.location) {
        return null;
    }

    const { protocol, origin, port } = window.location;

    if (protocol !== "http:" && protocol !== "https:") {
        return null;
    }

    if (DEV_SERVER_PORTS.has(port)) {
        return null;
    }

    return normalise(origin);
}

function resolveApiBaseUrl(): string {
    return (
        fromRuntimeOverride() ??
        fromBuildConfig() ??
        fromPageOrigin() ??
        DEVELOPMENT_FALLBACK
    );
}

/** The resolved API root, without a trailing slash. */
export const API_BASE_URL = resolveApiBaseUrl();

/**
 * Build an absolute API URL from a root-relative path.
 *
 * Prefer this over concatenating `API_BASE_URL` by hand: it tolerates a
 * missing leading slash, which is how the old string-concatenation call sites
 * produced silently wrong URLs.
 */
export function apiUrl(path: string): string {
    if (!path) {
        return API_BASE_URL;
    }

    return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}
