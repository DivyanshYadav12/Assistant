//! Microphone capture into an in-memory buffer, saved as WAV on demand.
//!
//! Design: `Recorder` starts a cpal input stream on creation and appends
//! f32 samples into a shared Vec while `recording` is true. `stop_and_save`
//! flips the flag, drains the buffer, and writes a 16-bit PCM WAV file.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use tracing::{info, warn};

pub struct Recorder {
    samples: Arc<Mutex<Vec<f32>>>,
    recording: Arc<AtomicBool>,
    sample_rate: u32,
    channels: u16,
    // Kept alive for the duration of the recorder; dropping it stops capture.
    _stream: cpal::Stream,
}

impl Recorder {
    /// Open the default input device and start streaming into the buffer.
    pub fn start() -> Result<Self> {
        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .context("no default microphone found")?;
        let config = device
            .default_input_config()
            .context("no default input config")?;

        info!(
            device = %device.name().unwrap_or_else(|_| "unknown".into()),
            rate = config.sample_rate().0,
            channels = config.channels(),
            "starting microphone capture"
        );

        let sample_rate = config.sample_rate().0;
        let channels = config.channels();
        let samples: Arc<Mutex<Vec<f32>>> = Arc::new(Mutex::new(Vec::new()));
        let recording = Arc::new(AtomicBool::new(true));

        let samples_cb = Arc::clone(&samples);
        let recording_cb = Arc::clone(&recording);

        let stream = device.build_input_stream(
            &config.into(),
            move |data: &[f32], _| {
                if recording_cb.load(Ordering::Relaxed) {
                    if let Ok(mut buf) = samples_cb.lock() {
                        buf.extend_from_slice(data);
                    }
                }
            },
            |err| warn!(?err, "audio stream error"),
            None,
        )?;
        stream.play()?;

        Ok(Self {
            samples,
            recording,
            sample_rate,
            channels,
            _stream: stream,
        })
    }

    /// Stop capturing and write everything recorded so far to `path` as
    /// 16-bit PCM WAV. Returns the number of samples written.
    pub fn stop_and_save(self, path: &std::path::Path) -> Result<usize> {
        self.recording.store(false, Ordering::Relaxed);
        let samples = self
            .samples
            .lock()
            .map_err(|_| anyhow::anyhow!("audio buffer poisoned"))?
            .clone();

        write_wav(path, &samples, self.sample_rate, self.channels)?;
        info!(?path, n = samples.len(), "saved recording");
        Ok(samples.len())
    }
}

/// Minimal WAV writer (16-bit PCM) — avoids an extra dependency.
fn write_wav(path: &std::path::Path, samples: &[f32], rate: u32, channels: u16) -> Result<()> {
    use std::io::Write;

    let bits_per_sample: u16 = 16;
    let byte_rate = rate * channels as u32 * (bits_per_sample as u32 / 8);
    let block_align = channels * (bits_per_sample / 8);
    let data_len = (samples.len() * 2) as u32;

    let mut f = std::fs::File::create(path)?;
    f.write_all(b"RIFF")?;
    f.write_all(&(36 + data_len).to_le_bytes())?;
    f.write_all(b"WAVE")?;
    f.write_all(b"fmt ")?;
    f.write_all(&16u32.to_le_bytes())?;
    f.write_all(&1u16.to_le_bytes())?; // PCM
    f.write_all(&channels.to_le_bytes())?;
    f.write_all(&rate.to_le_bytes())?;
    f.write_all(&byte_rate.to_le_bytes())?;
    f.write_all(&block_align.to_le_bytes())?;
    f.write_all(&bits_per_sample.to_le_bytes())?;
    f.write_all(b"data")?;
    f.write_all(&data_len.to_le_bytes())?;
    for s in samples {
        let v = (s.clamp(-1.0, 1.0) * i16::MAX as f32) as i16;
        f.write_all(&v.to_le_bytes())?;
    }
    Ok(())
}
