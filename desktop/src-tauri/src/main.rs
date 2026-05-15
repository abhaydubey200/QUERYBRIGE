#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, SystemTray, SystemTrayMenu, CustomMenuItem, SystemTrayEvent};
use std::process::Command;
use std::sync::Mutex;

struct AppState {
    backend_process: Mutex<Option<std::process::Child>>,
}

fn main() {
    let quit = CustomMenuItem::new("quit".to_string(), "Quit QueryBridge");
    let hide = CustomMenuItem::new("hide".to_string(), "Hide Window");
    let show = CustomMenuItem::new("show".to_string(), "Show Window");
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_item(hide)
        .add_native_item(tauri::SystemTrayMenuItem::Separator)
        .add_item(quit);

    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .manage(AppState {
            backend_process: Mutex::new(None),
        })
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::MenuItemClick { id, .. } => {
                match id.as_str() {
                    "quit" => {
                        std::process::exit(0);
                    }
                    "hide" => {
                        let window = app.get_window("main").unwrap();
                        window.hide().unwrap();
                    }
                    "show" => {
                        let window = app.get_window("main").unwrap();
                        window.show().unwrap();
                    }
                    _ => {}
                }
            }
            _ => {}
        })
        .setup(|app| {
            // Start background services: Backend, Postgres, Redis
            // Note: In a production build, these would be bundled binaries
            println!("Initializing QueryBridge Runtime Services...");
            
            // Example: Starting the backend
            // let child = Command::new("backend/venv/bin/python")
            //     .arg("backend/app/main.py")
            //     .spawn()
            //     .expect("Failed to start backend");
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_runtime_status])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
fn get_runtime_status() -> String {
    "Healthy".to_string()
}
