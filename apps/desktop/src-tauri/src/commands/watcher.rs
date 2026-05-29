use std::sync::Mutex;
use std::collections::HashMap;
use notify::{Config, Event, RecommendedWatcher, RecursiveMode, Watcher};
use std::sync::mpsc;

static WATCHERS: Mutex<Option<HashMap<String, RecommendedWatcher>>> = Mutex::new(None);

#[tauri::command]
pub fn start_daw_watcher(path: String) -> Result<(), String> {
    let (tx, rx) = mpsc::channel();

    let mut watcher = RecommendedWatcher::new(
        move |res: Result<Event, notify::Error>| {
            if let Ok(event) = res {
                let _ = tx.send(event);
            }
        },
        Config::default(),
    )
    .map_err(|e| e.to_string())?;

    watcher
        .watch(std::path::Path::new(&path), RecursiveMode::Recursive)
        .map_err(|e| e.to_string())?;

    let mut watchers = WATCHERS.lock().map_err(|e| e.to_string())?;
    if watchers.is_none() {
        *watchers = Some(HashMap::new());
    }
    watchers.as_mut().unwrap().insert(path, watcher);

    // spawn listener thread
    std::thread::spawn(move || {
        for event in rx {
            match event.kind {
                notify::EventKind::Modify(_) | notify::EventKind::Create(_) => {
                    // DAW project file changed — could trigger auto-backup
                    log::info!("DAW project modified: {:?}", event.paths);
                }
                _ => {}
            }
        }
    });

    Ok(())
}

#[tauri::command]
pub fn stop_daw_watcher() -> Result<(), String> {
    let mut watchers = WATCHERS.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut map) = *watchers {
        map.clear();
    }
    Ok(())
}
