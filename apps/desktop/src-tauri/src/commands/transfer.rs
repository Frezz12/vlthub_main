use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::Path;
use std::time::Instant;
use tauri::{AppHandle, Emitter};
use walkdir::WalkDir;
use sha2::{Sha256, Digest};

#[tauri::command]
pub async fn download_file(app: AppHandle, url: String, dest: String, label: String, token: Option<String>) -> Result<(), String> {
    tokio::task::spawn_blocking(move || -> Result<(), String> {
        let client = reqwest::blocking::Client::builder()
            .tcp_nodelay(true)
            .redirect(reqwest::redirect::Policy::none())
            .build()
            .map_err(|e| e.to_string())?;

        let mut req_builder = client.get(&url);
        if let Some(ref t) = token {
            req_builder = req_builder.header("Authorization", format!("Bearer {}", t));
        }

        let response = req_builder.send().map_err(|e| e.to_string())?;
        let status = response.status();
        if !status.is_success() {
            let body = response.text().unwrap_or_default();
            return Err(format!("HTTP {}: {}", status, body));
        }

        let total = response.content_length().unwrap_or(0);

        let mut file = File::create(&dest).map_err(|e| e.to_string())?;
        let mut downloaded: u64 = 0;
        let mut last_pct: u32 = 0;
        let mut last_emit = Instant::now();
        let throttle = std::time::Duration::from_millis(500);

        let mut reader = response;
        let mut buf = [0u8; 1_048_576];
        loop {
            let n = reader.read(&mut buf).map_err(|e| e.to_string())?;
            if n == 0 {
                break;
            }
            file.write_all(&buf[..n]).map_err(|e| e.to_string())?;
            downloaded += n as u64;
            if total > 0 {
                let pct = ((downloaded as f64 / total as f64) * 99.0) as u32;
                if pct != last_pct && last_emit.elapsed() >= throttle {
                    last_pct = pct;
                    last_emit = Instant::now();
                    let _ = app.emit("download-progress", serde_json::json!({
                        "label": &label,
                        "progress": pct,
                    }));
                }
            }
        }
        let _ = app.emit("download-progress", serde_json::json!({
            "label": &label,
            "progress": 100,
        }));
        Ok(())
    })
    .await
    .map_err(|e| format!("Download task failed: {}", e))?
}

fn should_exclude(relative_path: &str) -> bool {
    let lower = relative_path.to_lowercase();
    if lower.contains("__macosx") { return true; }
    if lower.ends_with(".ds_store") { return true; }
    if lower.ends_with("thumbs.db") { return true; }
    if lower.ends_with(".tmp") { return true; }
    if lower.ends_with(".temp") { return true; }
    if relative_path.starts_with('~') { return true; }
    if lower.contains("audio cache") { return true; }
    if lower.ends_with(".caf") { return true; }
    false
}

#[derive(serde::Serialize)]
pub struct UploadArchiveResult {
    pub file_hash: String,
    pub file_size: u64,
    pub file_id: Option<String>,
}

#[tauri::command]
pub async fn upload_archive_from_path(
    app: AppHandle,
    folder_path: String,
    project_id: String,
    version_id: String,
    token: String,
    file_name: String,
    api_base_url: String,
) -> Result<UploadArchiveResult, String> {
    eprintln!("[upload_archive] folder_path={folder_path}, project_id={project_id}, version_id={version_id}, file_name={file_name}, api_base_url={api_base_url}");

    tokio::task::spawn_blocking(move || -> Result<UploadArchiveResult, String> {
        let source_dir = Path::new(&folder_path);
        if !source_dir.is_dir() {
            let _ = app.emit("upload-error", serde_json::json!({
                "label": &version_id,
                "error": format!("Not a directory: {}", folder_path),
            }));
            return Err(format!("Not a directory: {}", folder_path));
        }

        // 1. Create archive in temp dir
        let temp_dir = std::env::temp_dir().join("pjasaver_upload");
        fs::create_dir_all(&temp_dir).map_err(|e| e.to_string())?;
        let zip_path = temp_dir.join(&file_name);

        let total_files: u32 = WalkDir::new(source_dir)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .filter(|e| {
                let rel = e.path().strip_prefix(source_dir).ok()
                    .map(|p| p.to_string_lossy())
                    .unwrap_or_default();
                !should_exclude(&rel)
            })
            .count() as u32;

        {
            let zip_file = File::create(&zip_path).map_err(|e| e.to_string())?;
            let mut zip = zip::ZipWriter::new(zip_file);
            let mut processed: u32 = 0;

            for entry in WalkDir::new(source_dir) {
                let entry = entry.map_err(|e| e.to_string())?;
                let relative = entry.path().strip_prefix(source_dir).map_err(|e| e.to_string())?;
                let relative_str = relative.to_string_lossy();

                if should_exclude(&relative_str) {
                    continue;
                }

                if entry.file_type().is_dir() {
                    zip.add_directory(relative_str.as_ref(), zip::write::FileOptions::<()>::default())
                        .map_err(|e| e.to_string())?;
                } else {
                    let mut f = File::open(entry.path()).map_err(|e| e.to_string())?;
                    zip.start_file(relative_str.as_ref(), zip::write::FileOptions::<()>::default())
                        .map_err(|e| e.to_string())?;
                    std::io::copy(&mut f, &mut zip).map_err(|e| e.to_string())?;

                    processed += 1;
                    if total_files > 0 {
                        let pct = ((processed as f64 / total_files as f64) * 30.0) as u32;
                        let _ = app.emit("upload-progress", serde_json::json!({
                            "label": &version_id,
                            "progress": pct,
                            "phase": "archive",
                        }));
                    }
                }
            }
            zip.finish().map_err(|e| e.to_string())?;
        }

        // 2. Compute SHA-256
        let file_hash = {
            let mut f = File::open(&zip_path).map_err(|e| e.to_string())?;
            let mut hasher = Sha256::new();
            std::io::copy(&mut f, &mut hasher).map_err(|e| e.to_string())?;
            format!("{:x}", hasher.finalize())
        };

        let file_size = fs::metadata(&zip_path).map_err(|e| e.to_string())?.len();
        let chunk_size: u64 = 8 * 1024 * 1024;

        // 3. Upload chunks
        let client = reqwest::blocking::Client::builder()
            .tcp_nodelay(true)
            .build()
            .map_err(|e| e.to_string())?;

        let mut file = File::open(&zip_path).map_err(|e| e.to_string())?;
        let mut offset: u64 = 0;
        let mut buf = vec![0u8; chunk_size as usize];
        let mut last_pct: u32 = 0;

        while offset < file_size {
            let n = file.read(&mut buf).map_err(|e| e.to_string())?;
            if n == 0 {
                break;
            }

            let chunk_url = format!(
                "{}/api/v1/projects/{}/versions/{}/upload/chunk",
                api_base_url, project_id, version_id
            );

            let form = reqwest::blocking::multipart::Form::new()
                .part("file", reqwest::blocking::multipart::Part::bytes(buf[..n].to_vec())
                    .file_name(file_name.clone()));

            let offset_str = offset.to_string();
            let size_str = file_size.to_string();
            let resp = client
                .put(&chunk_url)
                .query(&[("offset", &offset_str), ("total_size", &size_str)])
                .header("Authorization", format!("Bearer {}", token))
                .multipart(form)
                .send()
                .map_err(|e| e.to_string())?;

        let status = resp.status();
        if !status.is_success() {
            let body = resp.text().unwrap_or_default();
            let _ = app.emit("upload-error", serde_json::json!({
                "label": &version_id,
                "error": format!("Upload chunk at offset {}: HTTP {}: {}", offset, status, body),
            }));
            return Err(format!("Upload chunk at offset {}: HTTP {}: {}", offset, status, body));
        }

            let resp_json: serde_json::Value = resp.json().map_err(|e| e.to_string())?;
            offset += n as u64;

            let pct = 30 + ((offset as f64 / file_size as f64) * 70.0) as u32;
            if pct != last_pct {
                last_pct = pct;
                let _ = app.emit("upload-progress", serde_json::json!({
                    "label": &version_id,
                    "progress": pct,
                    "phase": "upload",
                }));
            }

        if resp_json.get("complete").and_then(|c| c.as_bool()).unwrap_or(false) {
            let file_id = resp_json.get("file_id")
                .and_then(|v| v.as_str().map(String::from));
            fs::remove_file(&zip_path).ok();
            let _ = app.emit("upload-progress", serde_json::json!({
                "label": &version_id,
                "progress": 100,
                "phase": "complete",
            }));
            return Ok(UploadArchiveResult { file_hash, file_size, file_id });
        }
    }

    fs::remove_file(&zip_path).ok();
    let _ = app.emit("upload-error", serde_json::json!({
        "label": &version_id,
        "error": "Upload finished but server did not confirm completion",
    }));
    Err("Upload finished but server did not confirm completion".into())
    })
    .await
    .map_err(|e| format!("Background task failed: {}", e))?
}

#[tauri::command]
pub fn upload_chunk(url: String, chunk_path: String, offset: u64) -> Result<(), String> {
    let path = Path::new(&chunk_path);
    let file_size = fs::metadata(path).map_err(|e| e.to_string())?.len();

    let mut file = File::open(path).map_err(|e| e.to_string())?;
    let mut buffer = Vec::with_capacity(file_size as usize);
    file.read_to_end(&mut buffer).map_err(|e| e.to_string())?;

    let client = reqwest::blocking::Client::new();
    let response = client
        .put(&url)
        .header("Content-Type", "application/octet-stream")
        .header("Content-Range", format!("bytes {}-{}/{}", offset, offset + buffer.len() as u64 - 1, "*"))
        .body(buffer)
        .send()
        .map_err(|e| e.to_string())?;

    if !response.status().is_success() {
        return Err(format!("Upload failed with status: {}", response.status()));
    }

    Ok(())
}

#[tauri::command]
pub fn resume_upload(_upload_id: String, chunk_path: String) -> Result<u64, String> {
    let path = Path::new(&chunk_path);
    if path.exists() {
        fs::metadata(path)
            .map(|m| m.len())
            .map_err(|e| e.to_string())
    } else {
        Ok(0)
    }
}
