use std::path::Path;
use std::fs;
use sha2::{Sha256, Digest};
use zip::ZipWriter;
use std::fs::File;

use walkdir::WalkDir;

#[derive(serde::Serialize)]
pub struct ProjectFile {
    pub path: String,
    pub size: u64,
    pub is_dir: bool,
}

#[derive(serde::Serialize)]
pub struct FileInfo {
    pub size: u64,
    pub is_dir: bool,
    pub modified: String,
}

#[tauri::command]
pub fn scan_directory(path: String) -> Result<Vec<ProjectFile>, String> {
    let dir = Path::new(&path);
    if !dir.is_dir() {
        return Err("Not a directory".into());
    }

    let mut files = Vec::new();
    for entry in WalkDir::new(dir).max_depth(1) {
        if let Ok(entry) = entry {
            files.push(ProjectFile {
                path: entry.path().to_string_lossy().to_string(),
                size: entry.metadata().map(|m| m.len()).unwrap_or(0),
                is_dir: entry.file_type().is_dir(),
            });
        }
    }
    Ok(files)
}

#[tauri::command]
pub fn get_file_info(path: String) -> Result<FileInfo, String> {
    let meta = fs::metadata(&path).map_err(|e| e.to_string())?;
    Ok(FileInfo {
        size: meta.len(),
        is_dir: meta.is_dir(),
        modified: meta
            .modified()
            .map(|t| {
                let d: chrono::DateTime<chrono::Utc> = t.into();
                d.to_rfc3339()
            })
            .unwrap_or_default(),
    })
}

#[tauri::command]
pub fn calculate_sha256(path: String) -> Result<String, String> {
    let mut file = File::open(&path).map_err(|e| e.to_string())?;
    let mut hasher = Sha256::new();
    std::io::copy(&mut file, &mut hasher).map_err(|e| e.to_string())?;
    Ok(format!("{:x}", hasher.finalize()))
}

#[tauri::command]
pub fn archive_project(path: String, dest: String) -> Result<String, String> {
    let source_dir = Path::new(&path);
    let zip_path = Path::new(&dest);

    let file = File::create(zip_path).map_err(|e| e.to_string())?;
    let mut zip = ZipWriter::new(file);

    for entry in WalkDir::new(source_dir) {
        let entry = entry.map_err(|e| e.to_string())?;
        let relative = entry.path().strip_prefix(source_dir).map_err(|e| e.to_string())?;

        if entry.file_type().is_dir() {
            zip.add_directory(relative.to_string_lossy().as_ref(), zip::write::FileOptions::<()>::default())
                .map_err(|e| e.to_string())?;
        } else {
            let mut f = File::open(entry.path()).map_err(|e| e.to_string())?;
            zip.start_file(relative.to_string_lossy(), zip::write::FileOptions::<()>::default())
                .map_err(|e| e.to_string())?;
            std::io::copy(&mut f, &mut zip).map_err(|e| e.to_string())?;
        }
    }

    zip.finish().map_err(|e| e.to_string())?;
    Ok(zip_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn extract_archive(path: String, dest: String) -> Result<(), String> {
    let zip_file = File::open(&path).map_err(|e| e.to_string())?;
    let mut archive = zip::ZipArchive::new(zip_file).map_err(|e| e.to_string())?;
    archive.extract(&dest).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn clean_temp_files(paths: Vec<String>) -> Result<(), String> {
    for p in paths {
        let path = Path::new(&p);
        if path.is_dir() {
            fs::remove_dir_all(path).ok();
        } else {
            fs::remove_file(path).ok();
        }
    }
    Ok(())
}
