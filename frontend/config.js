/**
 * VERIFAI Deployment Configuration
 * 
 * When deploying your backend to Render:
 * 1. You can paste your Render URL here, for example:
 *    const RENDER_BACKEND_URL = "https://verifai-backend.onrender.com";
 * 2. OR leave it empty if you configure rewrites in vercel.json.
 * 3. You can also override it at runtime in the browser console or UI via:
 *    localStorage.setItem("VERIFAI_API_BASE", "https://your-backend.onrender.com");
 */

const DEFAULT_RENDER_BACKEND_URL = "";

window.VERIFAI_API_BASE = (
  window.VERIFAI_API_BASE ||
  localStorage.getItem("VERIFAI_API_BASE") ||
  DEFAULT_RENDER_BACKEND_URL
).trim().replace(/\/+$/, "");

/**
 * Returns the fully qualified API URL for an endpoint.
 * @param {string} endpoint - e.g. "/api/verify" or "api/health"
 * @returns {string}
 */
window.getApiUrl = function(endpoint) {
  if (!endpoint) return "";
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return endpoint;
  }
  const base = (window.VERIFAI_API_BASE || "").trim().replace(/\/+$/, "");
  const path = endpoint.startsWith("/") ? endpoint : "/" + endpoint;
  return base ? `${base}${path}` : path;
};

/**
 * Returns the fully qualified URL for assets such as uploaded evidence or reports.
 * @param {string} path - e.g. "/uploads/demo.jpg"
 * @returns {string}
 */
window.getAssetUrl = function(path) {
  return window.getApiUrl(path);
};

console.log("[VERIFAI Config] Backend API Base:", window.VERIFAI_API_BASE || "(relative / reverse proxy)");
