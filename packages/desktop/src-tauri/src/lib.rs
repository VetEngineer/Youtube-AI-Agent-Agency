pub mod commands;
pub mod tray;

use std::sync::atomic::Ordering;
use tauri::Manager;
use tray::QuitRequested;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(QuitRequested(std::sync::atomic::AtomicBool::new(false)))
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            tray::setup_tray(app)?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::backend::check_docker_available,
            commands::backend::start_local_backend,
            commands::backend::stop_local_backend,
            commands::backend::get_local_backend_status,
            commands::file_system::validate_output_dir,
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let quit_requested = window
                    .app_handle()
                    .state::<QuitRequested>()
                    .0
                    .load(Ordering::SeqCst);

                if !quit_requested {
                    window.hide().ok();
                    api.prevent_close();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application")
}
