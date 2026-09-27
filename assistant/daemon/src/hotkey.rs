//! Global hotkey handling — Ctrl+Alt+Space toggles push-to-talk.
//!
//! First press: start recording. Second press: stop, save WAV to a temp
//! file, and notify the planner over IPC. The winit event loop is required
//! on Windows for hotkey events to be delivered.

use anyhow::Result;
use global_hotkey::{
    hotkey::{Code, HotKey, Modifiers},
    GlobalHotKeyEvent, GlobalHotKeyManager,
};
use tracing::{error, info};
use winit::application::ApplicationHandler;
use winit::event::WindowEvent;
use winit::event_loop::{ActiveEventLoop, ControlFlow, EventLoop};
use winit::window::WindowId;

use crate::audio::Recorder;
use crate::ipc;

struct DaemonApp {
    recorder: Option<Recorder>,
}

impl ApplicationHandler for DaemonApp {
    fn resumed(&mut self, _: &ActiveEventLoop) {}

    fn window_event(&mut self, _: &ActiveEventLoop, _: WindowId, _: WindowEvent) {}

    fn about_to_wait(&mut self, event_loop: &ActiveEventLoop) {
        // Poll hotkey events; winit wakes us regularly in Poll mode.
        if let Ok(event) = GlobalHotKeyEvent::receiver().try_recv() {
            if event.state == global_hotkey::HotKeyState::Pressed {
                self.toggle();
            }
        }
        event_loop.set_control_flow(ControlFlow::Poll);
    }
}

impl DaemonApp {
    fn toggle(&mut self) {
        match self.recorder.take() {
            None => match Recorder::start() {
                Ok(rec) => {
                    info!("recording started (press hotkey again to stop)");
                    self.recorder = Some(rec);
                }
                Err(e) => error!(?e, "failed to start recording"),
            },
            Some(rec) => {
                let path = std::env::temp_dir().join("aether_capture.wav");
                match rec.stop_and_save(&path) {
                    Ok(n) if n > 0 => {
                        info!("recording stopped, notifying planner");
                        if let Err(e) = ipc::notify_planner(&path) {
                            error!(?e, "failed to notify planner (is it running?)");
                        }
                    }
                    Ok(_) => info!("recording was empty, ignored"),
                    Err(e) => error!(?e, "failed to save recording"),
                }
            }
        }
    }
}

pub fn run_event_loop() -> Result<()> {
    let manager = GlobalHotKeyManager::new()?;
    let hotkey = HotKey::new(Some(Modifiers::CONTROL | Modifiers::ALT), Code::Space);
    manager.register(hotkey)?;
    info!("hotkey registered: Ctrl+Alt+Space (push-to-talk toggle)");

    let event_loop = EventLoop::new()?;
    event_loop.set_control_flow(ControlFlow::Poll);
    let mut app = DaemonApp { recorder: None };
    event_loop.run_app(&mut app)?;
    Ok(())
}
