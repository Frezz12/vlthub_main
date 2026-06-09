import { invoke } from "@tauri-apps/api/core";

const API_BASE =
  typeof __API_BASE_URL__ !== "undefined" && __API_BASE_URL__
    ? __API_BASE_URL__
    : "http://localhost:8000";

const DAW_SIGNATURES: Record<string, RegExp> = {
  "Logic Pro": /\.logicx$/i,
  "Ableton Live": /\.als$/i,
  "FL Studio": /\.flp$/i,
  Cubase: /\.cpr$/i,
  REAPER: /\.rpp$/i,
  "Studio One": /\.song$/i,
  Bitwig: /\.bwproject$/i,
};

const EXCLUDE_PATTERNS = [
  /__MACOSX/i,
  /\.DS_Store/i,
  /Thumbs\.db/i,
  /\.tmp$/i,
  /\.temp$/i,
  /^~/,
  /Audio cache/i,
  /\.caf$/i,
];

let cachedFiles: File[] | null = null;
let cachedTauriPath: string | null = null;
let pickedFolderName: string | null = null;

const DB_NAME = "PJSaver";
const STORE_NAME = "dirHandles";

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE_NAME);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function saveDirHandle(
  projectId: string,
  handle: FileSystemDirectoryHandle,
): Promise<void> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(handle, projectId);
    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // IndexedDB not available
  }
}

async function loadDirHandle(
  projectId: string,
): Promise<FileSystemDirectoryHandle | null> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    return new Promise((resolve) => {
      const req = tx.objectStore(STORE_NAME).get(projectId);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => resolve(null);
    });
  } catch {
    return null;
  }
}

function isTauri(): boolean {
  try {
    const hasTauri =
      typeof window !== "undefined" &&
      ((window as any).__TAURI__ !== undefined ||
        (window as any).__TAURI_INTERNALS__ !== undefined);
    console.log(
      "[isTauri] __TAURI__:",
      (window as any).__TAURI__,
      "__TAURI_INTERNALS__:",
      (window as any).__TAURI_INTERNALS__,
      "result:",
      hasTauri,
    );
    return hasTauri;
  } catch (e) {
    console.error("[isTauri] error:", e);
    return false;
  }
}

export function useProjectArchiver() {
  function getPickedFolderName(): string | null {
    return pickedFolderName;
  }

  function getCachedTauriPath(): string | null {
    return cachedTauriPath;
  }

  async function pickFolder(
    forcePick = false,
    projectId?: string,
    savedPath?: string,
  ): Promise<File[]> {
    if (!forcePick && cachedFiles && cachedFiles.length) {
      return cachedFiles;
    }

    // ---- Tauri native path ----
    if (isTauri()) {
      try {
        if (
          !forcePick &&
          savedPath &&
          (savedPath.includes("/") || savedPath.includes("\\"))
        ) {
          cachedTauriPath = savedPath;
        } else {
          const dirPath = await invoke<string | null>("pick_folder");
          if (!dirPath) return [];
          cachedTauriPath = dirPath;
        }
        const segments = cachedTauriPath!.replace(/\\/g, "/").split("/");
        pickedFolderName = segments[segments.length - 1] || "project";

        // Quick scan for DAW detection (just filenames, no content)
        const dawFiles: File[] = [];
        try {
          const filePaths = await invoke<string[]>("list_dir_recursive", {
            path: cachedTauriPath,
          });
          for (const fp of filePaths) {
            const name = fp.split(/[/\\]/).pop() || "file";
            dawFiles.push(new File([], name));
          }
        } catch {
          /* ignore */
        }
        cachedFiles = dawFiles;
        return dawFiles;
      } catch (e) {
        console.error("Tauri pick_folder failed:", e);
        return [];
      }
    }

    // ---- IndexedDB restore (browser) ----
    if (!forcePick && projectId) {
      const handle = await loadDirHandle(projectId);
      if (handle) {
        const files: File[] = [];
        const rootName = handle.name || "project";
        pickedFolderName = rootName;
        await walkDir(handle, rootName, files);
        cachedFiles = files;
        return files;
      }
    }

    // ---- Browser File System Access API ----
    try {
      if ("showDirectoryPicker" in window) {
        const handle = await (window as any).showDirectoryPicker();
        const files: File[] = [];
        const rootName = handle.name || "project";
        pickedFolderName = rootName;
        await walkDir(handle, rootName, files);
        cachedFiles = files;

        if (projectId) {
          await saveDirHandle(projectId, handle);
        }

        return files;
      }
    } catch {
      // Fall through to input fallback
    }

    // ---- Fallback: webkitdirectory input ----
    const input = document.createElement("input");
    input.type = "file";
    input.setAttribute("webkitdirectory", "");
    input.setAttribute("directory", "");
    return new Promise<File[]>((resolve) => {
      let resolved = false;
      input.addEventListener("change", () => {
        if (resolved) return;
        resolved = true;
        const files = Array.from(input.files || []);
        if (files.length) {
          const name = files[0].webkitRelativePath.split("/")[0];
          pickedFolderName = name;
        }
        cachedFiles = files;
        resolve(files);
      });
      input.click();
      setTimeout(() => {
        if (!resolved) {
          resolved = true;
          resolve([]);
        }
      }, 60000);
    });
  }

  function clearCache() {
    cachedFiles = null;
    cachedTauriPath = null;
    pickedFolderName = null;
  }

  function hasCache(): boolean {
    return cachedFiles !== null && cachedFiles.length > 0;
  }

  async function walkDir(handle: any, rootName: string, files: File[]) {
    for await (const entry of handle.values()) {
      if (entry.kind === "file") {
        const file = await entry.getFile();
        const relPath = entry.name;
        Object.defineProperty(file, "webkitRelativePath", {
          value: rootName + "/" + relPath,
        });
        files.push(file);
      } else if (entry.kind === "directory") {
        await walkDir(entry, rootName + "/" + entry.name, files);
      }
    }
  }

  function detectDaw(files: File[]): {
    daw: string | null;
    projectFile: File | null;
  } {
    for (const f of files) {
      for (const [daw, pattern] of Object.entries(DAW_SIGNATURES)) {
        if (pattern.test(f.name)) {
          return { daw, projectFile: f };
        }
      }
    }
    return { daw: null, projectFile: null };
  }

  function shouldInclude(file: File): boolean {
    return !EXCLUDE_PATTERNS.some(
      (p) => p.test(file.name) || p.test(file.webkitRelativePath),
    );
  }

  function getTauriArchivePath(): string | null {
    return cachedTauriPath;
  }

  async function archiveProjectFromPath(
    dirPath: string,
    onProgress?: (pct: number) => void,
  ): Promise<{ blob: Blob; sha256: string; totalSize: number }> {
    const tempDir = await invoke<string>("get_temp_dir");
    const zipName = `pjasaver_${Date.now()}.zip`;
    const zipPath = `${tempDir}\\${zipName}`;

    if (onProgress) onProgress(10);
    await invoke("archive_project", { path: dirPath, dest: zipPath });
    if (onProgress) onProgress(50);

    const bytes = await invoke<number[]>("read_file_bytes", { path: zipPath });
    const uint8 = new Uint8Array(bytes);
    const blob = new Blob([uint8]);
    if (onProgress) onProgress(70);

    const hashBuffer = await crypto.subtle.digest("SHA-256", uint8);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const sha256 = hashArray
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    if (onProgress) onProgress(85);

    try {
      await invoke("clean_temp_files", { paths: [zipPath] });
    } catch {
      /* ignore */
    }
    if (onProgress) onProgress(90);

    return { blob, sha256, totalSize: blob.size };
  }

  async function archiveProject(
    files: File[],
    onProgress?: (pct: number) => void,
    signal?: AbortSignal,
  ): Promise<{ blob: Blob; sha256: string; totalSize: number }> {
    const JSZip = (await import("jszip")).default;
    const zip = new JSZip();

    const toArchive = files.filter(shouldInclude);

    for (let i = 0; i < toArchive.length; i++) {
      if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
      const file = toArchive[i];
      const arrayBuffer = await file.arrayBuffer();
      const relativePath = file.webkitRelativePath || file.name;
      zip.file(relativePath, arrayBuffer);
      if (onProgress) {
        onProgress(Math.round(((i + 1) / toArchive.length) * 50));
      }
    }

    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");

    const blob = await zip.generateAsync({
      type: "blob",
      compression: "DEFLATE",
      compressionOptions: { level: 6 },
      onProgress: (meta) => {
        if (onProgress) {
          onProgress(50 + Math.round(meta.percent / 2));
        }
      },
    });

    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");

    const hashBuffer = await crypto.subtle.digest(
      "SHA-256",
      await blob.arrayBuffer(),
    );
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const sha256 = hashArray
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");

    return { blob, sha256, totalSize: blob.size };
  }

  async function uploadArchive(
    blob: Blob,
    projectId: string,
    versionId: string,
    accessToken: string,
    onProgress: (pct: number) => void,
    folderName?: string,
    signal?: AbortSignal,
  ): Promise<void> {
    const chunkSize = 8 * 1024 * 1024;
    const totalSize = blob.size;
    const totalChunks = Math.ceil(totalSize / chunkSize);

    const baseName =
      (folderName || pickedFolderName || `project_${projectId}`)
        .replace(/[^a-zA-Zа-яА-ЯёЁ0-9\s_-]/g, "")
        .trim()
        .replace(/\s+/g, "_")
        .slice(0, 48) || `project_${projectId.slice(0, 8)}`;
    const ts = Date.now();
    const fileName = `${baseName}_${ts}.zip`;

    for (let i = 0; i < totalChunks; i++) {
      if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
      const start = i * chunkSize;
      const end = Math.min(start + chunkSize, totalSize);
      const chunk = blob.slice(start, end);

      const formData = new FormData();
      formData.append("file", chunk, fileName);

      const params = new URLSearchParams({
        offset: String(start),
        total_size: String(totalSize),
      });

      const res = await fetch(
        `${API_BASE}/api/v1/projects/${projectId}/versions/${versionId}/upload/chunk?${params}`,
        {
          method: "PUT",
          headers: { Authorization: `Bearer ${accessToken}` },
          body: formData,
          signal,
        },
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload failed");
      }

      onProgress(Math.round(((i + 1) / totalChunks) * 100));
    }
  }

  async function uploadTauriArchiveFromPath(
    folderPath: string,
    projectId: string,
    versionId: string,
    accessToken: string,
    folderName?: string,
  ): Promise<{ fileHash?: string; fileId?: string }> {
    const baseName =
      (
        folderName ||
        folderPath
          .replace(/[/\\]$/, "")
          .split(/[/\\]/)
          .pop() ||
        `project_${projectId}`
      )
        .replace(/[^a-zA-Zа-яА-ЯёЁ0-9\s_-]/g, "")
        .trim()
        .replace(/\s+/g, "_")
        .slice(0, 48) || `project_${projectId.slice(0, 8)}`;
    const ts = Date.now();
    const fileName = `${baseName}_${ts}.zip`;
    const apiBaseUrl = API_BASE
    console.log("[uploadTauriArchiveFromPath] called with:", {
      folderPath,
      projectId,
      versionId,
      token: accessToken?.slice(0, 10) + "...",
      fileName,
      apiBaseUrl,
    });
    const result = await invoke<{
      file_hash: string;
      file_size: number;
      file_id: string | null;
    }>("upload_archive_from_path", {
      folderPath,
      projectId,
      versionId,
      token: accessToken,
      fileName,
      apiBaseUrl,
    });
    return { fileHash: result.file_hash, fileId: result.file_id || undefined };
  }

  return {
    pickFolder,
    detectDaw,
    shouldInclude,
    archiveProject,
    archiveProjectFromPath,
    uploadArchive,
    uploadTauriArchiveFromPath,
    clearCache,
    hasCache,
    getPickedFolderName,
    getCachedTauriPath,
    getTauriArchivePath,
  };
}
