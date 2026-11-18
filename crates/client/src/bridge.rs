use bevy::{platform::time::Instant, prelude::Resource};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use tc_session::{DEFAULT_SEED, MAX_TICKS, SimulationReport, Timing, VIEW_STRIDE};

#[derive(Clone, Debug, Deserialize, Serialize, Resource)]
#[serde(default, deny_unknown_fields)]
pub struct Options {
    pub units: usize,
    pub rigs: usize,
    pub seed: u32,
    pub ticks: u32,
    pub warmup: u32,
    pub width: u32,
    pub height: u32,
    pub fullscreen: bool,
    pub inspect: bool,
}

impl Default for Options {
    fn default() -> Self {
        Self {
            units: 500,
            rigs: 0,
            seed: DEFAULT_SEED,
            ticks: 0,
            warmup: 60,
            width: 1920,
            height: 1080,
            fullscreen: false,
            inspect: false,
        }
    }
}

impl Options {
    pub fn validate(&self) -> Result<(), &'static str> {
        if !matches!(self.units, 500 | 4_000) {
            return Err("units must be 500 or 4000");
        }
        if self.rigs > self.units || !self.rigs.is_multiple_of(2) {
            return Err("rigs must be an even number between zero and the unit count");
        }
        if self.ticks > MAX_TICKS || (self.ticks != 0 && self.warmup >= self.ticks) {
            return Err("timed runs require warmup < ticks <= 100000");
        }
        if !(320..=3840).contains(&self.width) || !(240..=2160).contains(&self.height) {
            return Err("resolution must be between 320×240 and 3840×2160");
        }
        Ok(())
    }
}

#[derive(Default, Clone, Serialize)]
pub struct Status {
    pub ready: bool,
    pub error: Option<String>,
    pub adapter: String,
    pub backend: String,
    pub tick: u32,
    pub rigs_ready: usize,
    pub colored_rigs: [usize; 2],
    pub clip: usize,
    pub pose_changes: [u32; 3],
}

#[derive(Serialize)]
pub struct RenderReport {
    pub options: Options,
    pub status: Status,
    pub actual_resolution: [u32; 2],
    pub frame: Timing,
    pub mean_frames_per_second: f64,
    pub render_update: Timing,
    pub view_queue: Timing,
    pub views_applied: u32,
    pub views_replaced: u32,
    pub simulation: SimulationReport,
}

pub(crate) struct View {
    pub tick: u32,
    pub queued: Instant,
    pub bytes: Vec<u8>,
}

#[derive(Default)]
pub(crate) struct Shared {
    pub status: Status,
    pub view: Option<View>,
    pub available: Vec<Vec<u8>>,
    pub replaced: u32,
    pub simulation: Option<SimulationReport>,
    pub report: Option<String>,
    pub selected_clip: Option<usize>,
}

#[derive(Clone, Resource)]
pub struct Bridge {
    pub(crate) state: Arc<Mutex<Shared>>,
    view_len: usize,
}

impl Bridge {
    pub fn new(units: usize) -> Self {
        let view_len = units * VIEW_STRIDE;
        let available = (0..3).map(|_| vec![0; view_len]).collect();
        Self {
            state: Arc::new(Mutex::new(Shared {
                available,
                ..Default::default()
            })),
            view_len,
        }
    }

    /// Keep the newest complete view. Fill the buffer outside the lock.
    pub fn publish(&self, tick: u32, fill: impl FnOnce(&mut [u8])) -> bool {
        let Some(mut bytes) = self.state.lock().unwrap().available.pop() else {
            return false;
        };
        fill(&mut bytes);
        let mut state = self.state.lock().unwrap();
        if let Some(stale) = state.view.replace(View {
            tick,
            queued: Instant::now(),
            bytes,
        }) {
            state.available.push(stale.bytes);
            state.replaced += 1;
        }
        true
    }

    pub fn view_len(&self) -> usize {
        self.view_len
    }

    pub fn finish(&self, report: SimulationReport) {
        self.state.lock().unwrap().simulation = Some(report);
    }

    pub fn report(&self) -> Option<String> {
        self.state.lock().unwrap().report.clone()
    }

    pub fn status(&self) -> Status {
        self.state.lock().unwrap().status.clone()
    }

    pub fn select_clip(&self, clip: Option<usize>) {
        assert!(clip.is_none_or(|index| index < 3));
        self.state.lock().unwrap().selected_clip = clip;
    }
}
