const { randomUUID } = require("node:crypto");

const MAX_REQUEST_BYTES = 4 * 1024 * 1024;
const MAX_IMAGE_BYTES = 3 * 1024 * 1024;
const MAX_COMPLAINTS = 100;
const MAX_STORED_BYTES = 20 * 1024 * 1024;
const RETENTION_MS = 24 * 60 * 60 * 1000;
const COMPLAINT_TYPES = new Set([
  "refund",
  "damaged_goods",
  "customer_support",
  "wrong_item",
  "delivery",
  "other"
]);
const STORE_KEY = Symbol.for("pet-guardian.temporary-complaints");

function getStore() {
  if (!globalThis[STORE_KEY]) globalThis[STORE_KEY] = new Map();
  return globalThis[STORE_KEY];
}

function sendJson(res, status, value) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(value));
}

async function readRequest(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_REQUEST_BYTES) {
      const error = new Error("The request is too large. Please use an image under 3 MB.");
      error.status = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  return Buffer.concat(chunks, size);
}

function parseMultipart(body, contentType) {
  const boundaryMatch = contentType.match(/boundary=(?:"([^"]+)"|([^;]+))/i);
  const boundary = boundaryMatch && (boundaryMatch[1] || boundaryMatch[2].trim());
  if (!boundary || boundary.length > 200) {
    const error = new Error("The form upload could not be read. Please try again.");
    error.status = 400;
    throw error;
  }

  const delimiter = Buffer.from(`--${boundary}`);
  const nextDelimiter = Buffer.from(`\r\n--${boundary}`);
  const fields = new Map();
  let file = null;
  let cursor = 0;

  while (cursor < body.length) {
    if (!body.subarray(cursor, cursor + delimiter.length).equals(delimiter)) {
      const error = new Error("The form upload is malformed.");
      error.status = 400;
      throw error;
    }

    cursor += delimiter.length;
    if (body.subarray(cursor, cursor + 2).toString() === "--") break;
    if (body.subarray(cursor, cursor + 2).toString() !== "\r\n") {
      const error = new Error("The form upload is malformed.");
      error.status = 400;
      throw error;
    }
    cursor += 2;

    const headersEnd = body.indexOf(Buffer.from("\r\n\r\n"), cursor);
    if (headersEnd === -1) {
      const error = new Error("The form upload is malformed.");
      error.status = 400;
      throw error;
    }

    const headers = body.subarray(cursor, headersEnd).toString("utf8");
    const disposition = headers.match(/content-disposition:\s*form-data;([^\r\n]+)/i);
    const fieldName = disposition && disposition[1].match(/(?:^|;)\s*name="([^"]+)"/i)?.[1];
    if (!fieldName) {
      const error = new Error("The form upload is malformed.");
      error.status = 400;
      throw error;
    }

    const filename = disposition[1].match(/(?:^|;)\s*filename="([^"]*)"/i)?.[1];
    const contentStart = headersEnd + 4;
    const contentEnd = body.indexOf(nextDelimiter, contentStart);
    if (contentEnd === -1) {
      const error = new Error("The form upload is malformed.");
      error.status = 400;
      throw error;
    }

    const value = body.subarray(contentStart, contentEnd);
    if (filename !== undefined) {
      if (fieldName !== "evidence" || file) {
        const error = new Error("Only one evidence image can be uploaded.");
        error.status = 400;
        throw error;
      }
      const type = headers.match(/content-type:\s*([^\r\n]+)/i)?.[1].trim().toLowerCase();
      file = { name: filename.slice(0, 200), type, data: Buffer.from(value) };
    } else {
      if (fields.has(fieldName)) {
        const error = new Error("The form contains a duplicate field.");
        error.status = 400;
        throw error;
      }
      fields.set(fieldName, value.toString("utf8"));
    }

    cursor = contentEnd + 2;
  }

  return { fields, file };
}

function validateImage(file) {
  if (file.data.length === 0) return null;
  if (file.data.length > MAX_IMAGE_BYTES) {
    const error = new Error("The image must be 3 MB or smaller.");
    error.status = 413;
    throw error;
  }

  const isJpeg = file.type === "image/jpeg" &&
    file.data[0] === 0xff && file.data[1] === 0xd8 && file.data[2] === 0xff;
  const isPng = file.type === "image/png" &&
    file.data.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
  const isWebp = file.type === "image/webp" &&
    file.data.subarray(0, 4).toString() === "RIFF" &&
    file.data.subarray(8, 12).toString() === "WEBP";

  if (!isJpeg && !isPng && !isWebp) {
    const error = new Error("The evidence must be a valid JPG, PNG, or WebP image.");
    error.status = 400;
    throw error;
  }

  return file;
}

function pruneStore(store, now) {
  for (const [id, complaint] of store) {
    if (complaint.createdAt < now - RETENTION_MS) store.delete(id);
  }

  let totalBytes = 0;
  for (const complaint of store.values()) {
    totalBytes += complaint.evidence?.data.length || 0;
  }
  return totalBytes;
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return sendJson(res, 405, { error: "Method not allowed" });
  }

  try {
    const contentType = req.headers["content-type"] || "";
    if (!contentType.toLowerCase().startsWith("multipart/form-data")) {
      return sendJson(res, 415, { error: "Submit the complaint as a multipart form." });
    }

    const body = await readRequest(req);
    const { fields, file: uploadedFile } = parseMultipart(body, contentType);
    const name = (fields.get("name") || "").trim();
    const email = (fields.get("email") || "").trim();
    const complaintType = fields.get("complaint_type") || "";
    const description = (fields.get("description") || "").trim();

    if (!name || name.length > 120) {
      return sendJson(res, 400, { error: "Enter a name of 1 to 120 characters." });
    }
    if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return sendJson(res, 400, { error: "Enter a valid email address." });
    }
    if (!COMPLAINT_TYPES.has(complaintType)) {
      return sendJson(res, 400, { error: "Select a valid complaint type." });
    }
    if (!description || description.length > 2000) {
      return sendJson(res, 400, { error: "Enter a description of 1 to 2000 characters." });
    }

    const evidence = uploadedFile ? validateImage(uploadedFile) : null;
    const store = getStore();
    const now = Date.now();
    let storedBytes = pruneStore(store, now);
    while (
      store.size >= MAX_COMPLAINTS ||
      storedBytes + (evidence?.data.length || 0) > MAX_STORED_BYTES
    ) {
      const oldestId = store.keys().next().value;
      if (!oldestId) {
        return sendJson(res, 503, { error: "Temporary complaint storage is full. Please try again later." });
      }
      const oldest = store.get(oldestId);
      storedBytes -= oldest.evidence?.data.length || 0;
      store.delete(oldestId);
    }

    const id = randomUUID();
    store.set(id, {
      id,
      name,
      email,
      complaintType,
      description,
      evidence,
      createdAt: now,
      expiresAt: now + RETENTION_MS
    });

    return sendJson(res, 201, {
      id,
      message: "Your complaint was accepted for temporary storage.",
      expiresAt: new Date(now + RETENTION_MS).toISOString()
    });
  } catch (error) {
    console.error("Complaint submission failed:", error.message);
    return sendJson(res, error.status || 500, {
      error: error.status ? error.message : "Could not submit the complaint. Please try again."
    });
  }
};

module.exports.config = {
  api: { bodyParser: false }
};
