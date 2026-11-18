use std::{error::Error, time::Instant};
use tc_session::{DEFAULT_SEED, MAX_TICKS, Replay, Timing};

fn main() -> Result<(), Box<dyn Error>> {
    let mut args = std::env::args().skip(1);
    let units = args.next().as_deref().unwrap_or("500").parse()?;
    let ticks: u32 = args.next().as_deref().unwrap_or("400").parse()?;
    let seed = args
        .next()
        .map(|seed| seed.parse())
        .transpose()?
        .unwrap_or(DEFAULT_SEED);
    if args.next().is_some() || !(1..=MAX_TICKS).contains(&ticks) {
        return Err("usage: tc-replay [500|4000] [ticks 1..100000] [seed u32]".into());
    }

    let mut replay = Replay::new(units, seed)?;
    let mut step = Vec::with_capacity(ticks as usize);
    for tick in 1..=ticks {
        let start = Instant::now();
        replay.step();
        step.push(start.elapsed().as_secs_f64() * 1000.0);
        replay.record(tick == ticks);
    }
    println!(
        "{}",
        serde_json::json!({"trace": replay.finish(), "step": Timing::from_samples(&mut step)})
    );
    Ok(())
}
