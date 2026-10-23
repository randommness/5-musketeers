(function () {
  const RAILWAY_API_URL = "https://5-musketeers-production.up.railway.app/";
  const isLocal = window.location.protocol === "file:" ||
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  const BASE_URL = isLocal ? RAILWAY_API_URL : `${window.location.origin}/`;

  async function request(path, options = {}) {
    const url = new URL(path, options.baseUrl || BASE_URL);
    Object.entries(options.query || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    });

    const requestOptions = { method: options.method || "GET" };
    if (options.body !== undefined) {
      if (options.body instanceof FormData) {
        requestOptions.body = options.body;
      } else {
        requestOptions.headers = { "Content-Type": "application/json" };
        requestOptions.body = JSON.stringify(options.body);
      }
    }

    const response = await fetch(url, requestOptions);
    const text = await response.text();
    let result = null;
    if (text) {
      try {
        result = JSON.parse(text);
      } catch {
        result = text;
      }
    }

    if (!response.ok) {
      const detail = typeof result === "string"
        ? result
        : result?.detail || result?.message;
      const error = new Error(`HTTP ${response.status}${detail ? `: ${detail}` : ""}`);
      error.status = response.status;
      error.response = result;
      throw error;
    }

    return result;
  }

  async function login(customerId, password) {
    const result = await request("/api/auth/login", {
      method: "POST",
      body: { customer_id: customerId, password }
    });

    if (typeof result === "boolean") return result;
    if (typeof result === "string" && /^(true|false)$/i.test(result.trim())) {
      return result.trim().toLowerCase() === "true";
    }
    if (result && typeof result === "object" && typeof result.authenticated === "boolean") {
      return result.authenticated;
    }

    const error = new Error("Unexpected login response: expected a boolean or an authenticated boolean");
    error.response = result;
    throw error;
  }

  function getCustomer(customerId) {
    if (!customerId) throw new Error("A customer ID is required to load customer information");
    return request("/api/customers", {
      query: { customer_id: customerId }
    });
  }

  function submitComplaint(formData) {
    if (window.location.protocol === "file:") {
      throw new Error("Complaint submissions require a deployed site or a local Vercel server");
    }
    return request("/api/complaints", {
      method: "POST",
      body: formData,
      baseUrl: `${window.location.origin}/`
    });
  }

  window.PET_API = { request, login, getCustomer, submitComplaint };
})();