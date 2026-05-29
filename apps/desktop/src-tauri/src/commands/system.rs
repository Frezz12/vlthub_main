use tauri::Manager;
use tauri_plugin_dialog::DialogExt;
use tokio::sync::oneshot;
use std::env;
use std::fs;
use std::path::Path;
use std::process::Command;
use walkdir::WalkDir;

#[tauri::command]
pub async fn pick_folder(app: tauri::AppHandle) -> Option<String> {
    let (tx, rx) = oneshot::channel();
    app.dialog()
        .file()
        .pick_folder(move |path| {
            let _ = tx.send(path);
        });
    rx.await.ok().flatten().map(|f| f.to_string())
}

#[tauri::command]
pub async fn save_file_dialog(app: tauri::AppHandle, default_name: String) -> Option<String> {
    let (tx, rx) = oneshot::channel();
    app.dialog()
        .file()
        .add_filter("All Files", &["*"])
        .set_file_name(&default_name)
        .save_file(move |path| {
            let _ = tx.send(path);
        });
    rx.await.ok().flatten().map(|f| f.to_string())
}

#[tauri::command]
pub fn write_binary_file(path: String, bytes: Vec<u8>) -> Result<(), String> {
    let target = Path::new(&path);
    if let Some(parent) = target.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(target, bytes).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn read_file_bytes(path: String) -> Result<Vec<u8>, String> {
    fs::read(&path).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_dir_recursive(path: String) -> Result<Vec<String>, String> {
    let dir = Path::new(&path);
    if !dir.is_dir() {
        return Err("Not a directory".into());
    }
    let mut files = Vec::new();
    for entry in WalkDir::new(dir) {
        let entry = entry.map_err(|e| e.to_string())?;
        if entry.file_type().is_file() {
            files.push(entry.path().to_string_lossy().to_string());
        }
    }
    Ok(files)
}

#[tauri::command]
pub fn get_temp_dir() -> String {
    env::temp_dir().to_string_lossy().to_string()
}

#[tauri::command]
pub fn open_devtools(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.open_devtools();
        Ok(())
    } else {
        Err("Main window not found".into())
    }
}

#[tauri::command]
pub fn open_in_browser(url: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args(["/c", "start", &url])
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&url)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    {
        Command::new("xdg-open")
            .arg(&url)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub fn open_in_file_manager(path: String) -> Result<(), String> {
    let target = Path::new(&path);
    let target_for_open = if target.is_file() {
        target.parent().unwrap_or(target)
    } else {
        target
    };

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(target_for_open)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(target_for_open)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    {
        Command::new("xdg-open")
            .arg(target_for_open)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    Ok(())
}
