//! IPC to the Python planner — Phase 1 uses a JSON-lines message over
//! localhost TCP (port 48100). Upgraded to gRPC/named pipes in Phase 2.

use std::io::Write;
use std::net::TcpStream;
use std::path::Path;

use anyhow::{Context, Result};
use serde::Serialize;

pub const PLANNER_ADDR: &str = "127.0.0.1:48100";

#[derive(Serialize)]
struct AudioCapturedMsg<'a> {
    r#type: &'static str,
    wav_path: &'a str,
}

/// Tell the planner a new capture is ready for transcription.
pub fn notify_planner(wav_path: &Path) -> Result<()> {
    let mut stream = TcpStream::connect(PLANNER_ADDR)
        .with_context(|| format!("planner not reachable at {PLANNER_ADDR}"))?;
    let msg = AudioCapturedMsg {
        r#type: "audio_captured",
        wav_path: wav_path.to_str().context("non-utf8 temp path")?,
    };
    let line = serde_json::to_string(&msg)?;
    stream.write_all(line.as_bytes())?;
    stream.write_all(b"\n")?;
    Ok(())
}
