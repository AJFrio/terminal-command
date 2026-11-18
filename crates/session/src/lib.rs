use serde::{Deserialize, Serialize};
use tc_sim::{ArmyOrder, Sim};

pub use tc_sim::{ARENA_METERS, TICK_MS, VIEW_STRIDE};

pub const DEFAULT_SEED: u32 = 21_041;
pub const HASH_INTERVAL: u32 = 20;
pub const MAX_TICKS: u32 = 100_000;
const ORDER_INTERVAL: u32 = 112;

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommandBatch {
    pub version: u8,
    pub tick: u32,
    pub player: u8,
    pub advance: bool,
    pub lane_mm: i32,
}

impl CommandBatch {
    pub const VERSION: u8 = 1;

    fn army_order(self) -> ArmyOrder {
        ArmyOrder {
            player: self.player,
            advance: self.advance,
            lane_mm: self.lane_mm,
        }
    }
}

pub struct Replay {
    sim: Sim,
    total: usize,
    seed: u32,
    hashes: Vec<Checkpoint>,
}

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq)]
pub struct Checkpoint {
    pub tick: u32,
    pub hash: String,
}

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq)]
pub struct Trace {
    pub version: u8,
    pub seed: u32,
    pub units: usize,
    pub ticks: u32,
    pub orders: u32,
    pub moving: u32,
    pub fired: u64,
    pub hits: u64,
    pub redeployed: u64,
    pub peak_projectiles: usize,
    pub hashes: Vec<Checkpoint>,
}

#[derive(Debug, Default, Serialize, Deserialize)]
pub struct Timing {
    pub samples: usize,
    pub mean_ms: f64,
    pub p50_ms: f64,
    pub p95_ms: f64,
    pub p99_ms: f64,
    pub max_ms: f64,
}

impl Timing {
    pub fn from_samples(samples: &mut [f64]) -> Self {
        if samples.is_empty() {
            return Self::default();
        }
        samples.sort_unstable_by(f64::total_cmp);
        let count = samples.len();
        let percentile = |percent| samples[count.saturating_mul(percent).div_ceil(100) - 1];
        Self {
            samples: count,
            mean_ms: samples.iter().sum::<f64>() / count as f64,
            p50_ms: percentile(50),
            p95_ms: percentile(95),
            p99_ms: percentile(99),
            max_ms: samples[count - 1],
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SimulationReport {
    pub trace: Trace,
    pub snapshot_bytes: usize,
    pub missed_deadlines: u32,
    pub skipped_transfers: u32,
    pub step: Timing,
    pub snapshot: Timing,
    pub worker_copy: Option<Timing>,
    pub worker_memory_bytes: Option<usize>,
}

impl Replay {
    pub fn new(total: usize, seed: u32) -> Result<Self, &'static str> {
        if !matches!(total, 500 | 4_000) {
            return Err("benchmark workload must contain 500 or 4000 units");
        }
        let sim = Sim::new(total, u64::from(seed));
        let mut replay = Self {
            sim,
            total,
            seed,
            hashes: Vec::new(),
        };
        replay.checkpoint();
        Ok(replay)
    }

    pub fn step(&mut self) {
        let next = self.tick() + 1;
        if (next - 1).is_multiple_of(ORDER_INTERVAL) {
            let phase = (next - 1) / ORDER_INTERVAL;
            let orders = [0_u8, 1].map(|player| {
                let mixed = self.seed.rotate_left(phase % 32) ^ (phase.wrapping_mul(0x9e3779b9));
                let lane = (mixed % 12_001) as i32 - 6_000;
                CommandBatch {
                    version: CommandBatch::VERSION,
                    tick: next,
                    player,
                    advance: phase.is_multiple_of(2),
                    lane_mm: if player == 0 { lane } else { -lane },
                }
                .army_order()
            });
            self.sim.step(&orders);
        } else {
            self.sim.step(&[]);
        }
    }

    /// Capture parity outside the measured simulation step.
    pub fn record(&mut self, final_tick: bool) {
        if final_tick || self.tick().is_multiple_of(HASH_INTERVAL) {
            self.checkpoint();
        }
    }

    fn checkpoint(&mut self) {
        self.hashes.push(Checkpoint {
            tick: self.tick(),
            hash: format!("{:016x}", self.sim.state_hash()),
        });
    }

    pub fn tick(&self) -> u32 {
        self.sim.tick()
    }

    pub fn view_len(&self) -> usize {
        self.total * VIEW_STRIDE
    }

    pub fn write_view(&self, dest: &mut [u8]) {
        self.sim.write_view(dest);
    }

    pub fn finish(self) -> Trace {
        let counts = self.sim.counts();
        Trace {
            version: CommandBatch::VERSION,
            seed: self.seed,
            units: self.total,
            ticks: self.sim.tick(),
            orders: counts.orders,
            moving: counts.moving,
            fired: counts.fired,
            hits: counts.hits,
            redeployed: counts.redeployed,
            peak_projectiles: counts.peak_projectiles,
            hashes: self.hashes,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn replay_exercises_movement_combat_and_reinforcement_at_both_scales() {
        for units in [500, 4_000] {
            let mut replay = Replay::new(units, DEFAULT_SEED).unwrap();
            let mut before = vec![0; replay.view_len()];
            let mut after = before.clone();
            replay.write_view(&mut before);

            for tick in 1..=400 {
                replay.step();
                replay.record(tick == 400);
            }
            replay.write_view(&mut after);
            assert_ne!(before, after);
            let trace = replay.finish();
            assert_eq!(trace.orders, 8);
            assert!(trace.moving > 0 && trace.hits > 0 && trace.redeployed > 0);
            assert!(trace.peak_projectiles > 0);
            assert_eq!(trace.hashes.len(), 21);
            assert_eq!(trace.hashes.last().unwrap().tick, 400);
        }
    }
}
