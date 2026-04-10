use std::sync::atomic::Ordering;
use tauri::{
    image::Image,
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager,
};

pub struct QuitRequested(pub std::sync::atomic::AtomicBool);

pub fn setup_tray(app: &tauri::App) -> tauri::Result<()> {
    let open_i = MenuItemBuilder::with_id("open", "열기").build(app)?;
    let quit_i = MenuItemBuilder::with_id("quit", "종료").build(app)?;

    let menu = MenuBuilder::new(app)
        .item(&open_i)
        .separator()
        .item(&quit_i)
        .build()?;

    // 아이콘을 컴파일 타임에 임베딩 (dev/release 경로 문제 회피)
    let icon_bytes = include_bytes!("../../icons/32x32.png");
    let icon = Image::from_bytes(icon_bytes)?;

    TrayIconBuilder::with_id("main_tray")
        .tooltip("YouTube AI Agent Agency")
        .icon(icon)
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "open" => {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.unminimize();
                    let _ = window.set_focus();
                }
            }
            "quit" => {
                app.state::<QuitRequested>()
                    .0
                    .store(true, Ordering::SeqCst);
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.unminimize();
                    let _ = window.set_focus();
                }
            }
        })
        .build(app)?;

    Ok(())
}
