mod commands;
mod daemon;

use crate::commands::cancel_download;
use commands::{
    archive_project, calculate_sha256, clean_temp_files, download_file, extract_archive,
    get_file_info, get_temp_dir, list_dir_recursive, open_devtools, open_in_browser,
    open_in_file_manager, pick_folder, read_file_bytes, resume_upload, save_file_dialog,
    scan_directory, start_daw_watcher, stop_daw_watcher, upload_archive_from_path,
    upload_chunk, write_binary_file,
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_deep_link::init())
        .invoke_handler(tauri::generate_handler![
            scan_directory,
            archive_project,
            extract_archive,
            get_file_info,
            get_temp_dir,
            calculate_sha256,
            clean_temp_files,
            pick_folder,
            save_file_dialog,
            upload_chunk,
            download_file,
            cancel_download,
            resume_upload,
            upload_archive_from_path,
            start_daw_watcher,
            stop_daw_watcher,
            write_binary_file,
            read_file_bytes,
            list_dir_recursive,
            open_in_file_manager,
            open_in_browser,
            open_devtools,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
