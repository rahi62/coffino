export const ACCESS_TOKEN_KEY = "cafino_access";
export const REFRESH_TOKEN_KEY = "cafino_refresh";

export function readSession(storage) {
  if (!storage) return { access: null, refresh: null };
  return {
    access: storage.getItem(ACCESS_TOKEN_KEY),
    refresh: storage.getItem(REFRESH_TOKEN_KEY),
  };
}

export function writeSession(storage, pair) {
  if (!storage || !pair?.access) throw new Error("invalid_session");
  storage.setItem(ACCESS_TOKEN_KEY, String(pair.access));
  if (pair.refresh) storage.setItem(REFRESH_TOKEN_KEY, String(pair.refresh));
}

export function clearSessionStorage(storage) {
  if (!storage) return;
  storage.removeItem(ACCESS_TOKEN_KEY);
  storage.removeItem(REFRESH_TOKEN_KEY);
}

export function createRefreshCoordinator({ storage, fetchImpl, refreshUrl }) {
  let inFlight = null;
  return async function refresh() {
    if (inFlight) return inFlight;
    inFlight = (async () => {
      const current = readSession(storage);
      if (!current.refresh) throw new Error("missing_refresh_token");
      const response = await fetchImpl(refreshUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: current.refresh }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("refresh_failed");
      const payload = await response.json();
      if (!payload?.access) throw new Error("refresh_invalid_payload");
      writeSession(storage, {
        access: payload.access,
        refresh: payload.refresh || current.refresh,
      });
      return String(payload.access);
    })();
    try {
      return await inFlight;
    } catch (error) {
      clearSessionStorage(storage);
      throw error;
    } finally {
      inFlight = null;
    }
  };
}

export async function requestWithOneRefresh({ request, refresh, getAccessToken }) {
  let response = await request(getAccessToken());
  if (response.status !== 401) return response;
  await refresh();
  response = await request(getAccessToken());
  return response;
}
