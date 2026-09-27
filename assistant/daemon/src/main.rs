//! Aether daemon — Phase 1 skeleton.
//!
//! Responsibilities (Phase 1):
//! 1. Register a global hotkey (Ctrl+Alt+Space) — "push to talk".
//! 2. Capture microphone audio into a ring buffer while the hotkey session is active.
//! 3. Write the captured audio to a WAV file and notify the Python planner
//!    over a localhost TCP socket (JSON lines protocol).
//!
//! Later phases move to gRPC + wake word + streaming STT.

mod audio;
mod hotkey;
mod ipc;

use anyhow::Result;
use tracing::info;

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info".into()),
        )
        .init();

    info!("Aether daemon starting");

    // The hotkey listener owns the OS event loop (must run on the main thread
    // on Windows). Audio capture + IPC run on background threads it spawns.
    hotkey::run_event_loop()
}
