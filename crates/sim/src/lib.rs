//! Deterministic, renderer-free benchmark simulation.

pub const TICK_MS: u32 = 50;
pub const VIEW_STRIDE: usize = 12;
pub const ARENA_METERS: f32 = 320.0;

const LIMIT: i32 = 160_000;
const CELL: i32 = 8_000;
const GRID_WIDTH: usize = (2 * LIMIT / CELL + 1) as usize;
const RANGE_SQUARED: i32 = 7_600 * 7_600;
const MAX_NEIGHBORS_PER_CELL: usize = 12;
const HEALTH: u16 = 100;

#[derive(Clone, Copy)]
pub struct ArmyOrder {
    pub player: u8,
    pub advance: bool,
    pub lane_mm: i32,
}

#[derive(Clone, Copy, Default)]
struct Point {
    x: i32,
    z: i32,
}

struct Unit {
    position: Point,
    goal: Point,
    slot: Point,
    hp: u16,
    generation: u32,
    next_shot: u32,
    firing_until: u32,
    speed: i32,
    heading: u8,
    moving: bool,
}

struct Shot {
    target: u32,
    generation: u32,
    due: u32,
}

#[derive(Default, Clone, Copy)]
pub struct Counts {
    pub orders: u32,
    pub moving: u32,
    pub fired: u64,
    pub hits: u64,
    pub redeployed: u64,
    pub peak_projectiles: usize,
}

pub struct Sim {
    tick: u32,
    rng: u64,
    army_size: usize,
    units: Vec<Unit>,
    shots: Vec<Shot>,
    grid: Vec<[Vec<usize>; 2]>,
    counts: Counts,
}

impl Sim {
    pub fn new(total: usize, seed: u64) -> Self {
        assert!((2..=4_000).contains(&total) && total.is_multiple_of(2));
        let mut rng = seed;
        let army_size = total / 2;
        let columns = if total <= 500 { 25 } else { 50 };
        let units = (0..total)
            .map(|id| {
                let player = id / army_size;
                let index = id % army_size;
                let side = if player == 0 { -1 } else { 1 };
                let slot = Point {
                    x: (index / columns) as i32 * 2_500,
                    z: (index % columns) as i32 * 2_800 - (columns as i32 - 1) * 1_400
                        + player as i32 * 900,
                };
                let home = Point {
                    x: side * (28_000 + slot.x),
                    z: slot.z,
                };
                rng = rng.wrapping_mul(6364136223846793005).wrapping_add(1);
                Unit {
                    position: home,
                    goal: home,
                    slot,
                    hp: HEALTH,
                    generation: 0,
                    next_shot: ((rng >> 32) % 15) as u32,
                    firing_until: 0,
                    speed: 890 + ((rng >> 48) % 81) as i32,
                    heading: if player == 0 { 2 } else { 6 },
                    moving: false,
                }
            })
            .collect();

        Self {
            tick: 0,
            rng,
            army_size,
            units,
            shots: Vec::with_capacity(total),
            grid: (0..GRID_WIDTH * GRID_WIDTH)
                .map(|_| [Vec::new(), Vec::new()])
                .collect(),
            counts: Counts::default(),
        }
    }

    pub fn tick(&self) -> u32 {
        self.tick
    }

    pub fn counts(&self) -> Counts {
        self.counts
    }

    pub fn step(&mut self, orders: &[ArmyOrder]) {
        self.tick += 1;
        for order in orders {
            let player = usize::from(order.player);
            assert!(player < 2 && (-20_000..=20_000).contains(&order.lane_mm));
            let side = if player == 0 { -1 } else { 1 };
            let anchor = if order.advance { -43_000 } else { 28_000 };
            let start = player * self.army_size;
            for unit in &mut self.units[start..start + self.army_size] {
                unit.goal = Point {
                    x: side * (anchor + unit.slot.x),
                    z: unit.slot.z + order.lane_mm,
                };
            }
            self.counts.orders += 1;
        }

        self.counts.moving = 0;
        for bucket in &mut self.grid {
            bucket[0].clear();
            bucket[1].clear();
        }
        for (id, unit) in self.units.iter_mut().enumerate() {
            let dx = unit.goal.x - unit.position.x;
            let dz = unit.goal.z - unit.position.z;
            let largest_axis = dx.abs().max(dz.abs());
            unit.moving = largest_axis != 0;
            if unit.moving {
                let travel = unit.speed.min(largest_axis);
                unit.position.x += dx * travel / largest_axis;
                unit.position.z += dz * travel / largest_axis;
                unit.heading = heading(dx, dz);
                self.counts.moving += 1;
            }
            let (x, z) = cell(unit.position);
            self.grid[z * GRID_WIDTH + x][id / self.army_size].push(id);
        }

        for id in 0..self.units.len() {
            // Acquisition is spread over four ticks in stable ID order.
            if id % 4 != self.tick as usize % 4 || self.units[id].next_shot > self.tick {
                continue;
            }
            if let Some(target) = self.target(id) {
                self.shots.push(Shot {
                    target: target as u32,
                    generation: self.units[target].generation,
                    due: self.tick + 3,
                });
                self.units[id].next_shot = self.tick + 12;
                self.units[id].firing_until = self.tick + 8;
                self.counts.fired += 1;
            }
        }
        self.counts.peak_projectiles = self.counts.peak_projectiles.max(self.shots.len());

        self.shots.retain(|shot| {
            if shot.due > self.tick {
                return true;
            }
            let id = shot.target as usize;
            let unit = &mut self.units[id];
            if unit.generation == shot.generation {
                self.counts.hits += 1;
                unit.hp = unit.hp.saturating_sub(18);
                if unit.hp == 0 {
                    // Synthetic reinforcements retain the slot and order so load stays constant.
                    let side = if id < self.army_size { -1 } else { 1 };
                    unit.position = Point {
                        x: side * (28_000 + unit.slot.x),
                        z: unit.slot.z,
                    };
                    unit.hp = HEALTH;
                    unit.generation += 1;
                    unit.next_shot = self.tick + 12;
                    unit.firing_until = 0;
                    self.counts.redeployed += 1;
                }
            }
            false
        });
    }

    fn target(&self, id: usize) -> Option<usize> {
        let position = self.units[id].position;
        let opponent = 1 - id / self.army_size;
        let (x, z) = cell(position);
        let mut best = None;
        for row in z.saturating_sub(1)..=(z + 1).min(GRID_WIDTH - 1) {
            for col in x.saturating_sub(1)..=(x + 1).min(GRID_WIDTH - 1) {
                for &candidate in self.grid[row * GRID_WIDTH + col][opponent]
                    .iter()
                    .take(MAX_NEIGHBORS_PER_CELL)
                {
                    let enemy = self.units[candidate].position;
                    let dx = position.x - enemy.x;
                    let dz = position.z - enemy.z;
                    if dx.abs() > 7_600 || dz.abs() > 7_600 {
                        continue;
                    }
                    let distance = dx * dx + dz * dz;
                    let key = (distance, candidate);
                    if distance <= RANGE_SQUARED && best.is_none_or(|previous| key < previous) {
                        best = Some(key);
                    }
                }
            }
        }
        best.map(|(_, index)| index)
    }

    /// Tick-tagged by the caller, with fixed-size records in unit ID order.
    pub fn write_view(&self, bytes: &mut [u8]) {
        assert_eq!(bytes.len(), self.units.len() * VIEW_STRIDE);
        for (id, (unit, record)) in self
            .units
            .iter()
            .zip(bytes.chunks_exact_mut(VIEW_STRIDE))
            .enumerate()
        {
            record[..4].copy_from_slice(&unit.position.x.to_le_bytes());
            record[4..8].copy_from_slice(&unit.position.z.to_le_bytes());
            record[8] = unit.heading;
            record[9] = (id / self.army_size) as u8;
            record[10] = if unit.firing_until > self.tick {
                2
            } else {
                u8::from(unit.moving)
            };
            record[11] = 0;
        }
    }

    /// FNV-1a over explicitly encoded little-endian fields. Grid and counters are derived.
    pub fn state_hash(&self) -> u64 {
        let mut hash = StateHash(0xcbf29ce484222325);
        hash.add(self.tick.to_le_bytes());
        hash.add(self.rng.to_le_bytes());
        hash.add((self.units.len() as u32).to_le_bytes());
        for unit in &self.units {
            for value in [
                unit.position.x,
                unit.position.z,
                unit.goal.x,
                unit.goal.z,
                unit.slot.x,
                unit.slot.z,
                unit.speed,
            ] {
                hash.add(value.to_le_bytes());
            }
            hash.add(unit.hp.to_le_bytes());
            hash.add(unit.generation.to_le_bytes());
            hash.add(unit.next_shot.to_le_bytes());
            hash.add(unit.firing_until.to_le_bytes());
            hash.add([unit.heading, u8::from(unit.moving)]);
        }
        hash.add((self.shots.len() as u32).to_le_bytes());
        for shot in &self.shots {
            hash.add(shot.target.to_le_bytes());
            hash.add(shot.generation.to_le_bytes());
            hash.add(shot.due.to_le_bytes());
        }
        hash.0
    }
}

fn cell(point: Point) -> (usize, usize) {
    (
        ((point.x + LIMIT) / CELL) as usize,
        ((point.z + LIMIT) / CELL) as usize,
    )
}

fn heading(x: i32, z: i32) -> u8 {
    if x.abs() > 2 * z.abs() {
        return if x > 0 { 2 } else { 6 };
    }
    if z.abs() > 2 * x.abs() {
        return if z > 0 { 0 } else { 4 };
    }
    match (x > 0, z > 0) {
        (true, true) => 1,
        (true, false) => 3,
        (false, false) => 5,
        (false, true) => 7,
    }
}

struct StateHash(u64);

impl StateHash {
    fn add(&mut self, bytes: impl IntoIterator<Item = u8>) {
        for byte in bytes {
            self.0 ^= u64::from(byte);
            self.0 = self.0.wrapping_mul(0x100000001b3);
        }
    }
}
