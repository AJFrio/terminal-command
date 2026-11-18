import init, { Simulation } from "./pkg/worker.js";
import { timing } from "./timing.js";

const TICK_MS = 50;
let recycle = [];

self.onmessage = ({ data }) => {
    if (data.kind === "recycle") {
        recycle.push(data.buffer);
    } else if (data.kind === "start") {
        run(data.options, data.headless).catch(reportError);
    }
};

function reportError(error) {
    self.postMessage({ kind: "error", message: String(error) });
}

async function run(options, headless) {
    const { memory } = await init();
    const simulation = new Simulation(options.units, options.seed);
    const snapshotBytes = simulation.view_len();
    const steps = [];
    const snapshots = [];
    const copies = [];
    let missed = 0;
    let skipped = 0;

    if (headless) {
        for (let tick = 1; tick <= options.ticks; tick++) {
            const start = performance.now();
            simulation.step();
            steps.push(performance.now() - start);
            simulation.record(tick === options.ticks);
        }
        self.postMessage({
            kind: "headless",
            report: {
                trace: JSON.parse(simulation.finish()),
                step: timing(steps),
                worker_memory_bytes: memory.buffer.byteLength,
            },
        });
        simulation.free();
        return;
    }

    recycle = Array.from({ length: 3 }, () => new ArrayBuffer(snapshotBytes));
    let deadline = performance.now();
    let tick = 0;
    function frame() {
        const now = performance.now();
        if (now < deadline) {
            setTimeout(pacedFrame, Math.ceil(deadline - now));
            return;
        }
        deadline += TICK_MS;
        tick++;
        const finalTick = tick === options.ticks;
        const measured = options.ticks !== 0 && tick > options.warmup;
        const start = performance.now();
        simulation.step();
        if (measured) steps.push(performance.now() - start);
        if (options.ticks) simulation.record(finalTick);
        const buffer = recycle.pop();
        if (buffer) {
            const startSnapshot = performance.now();
            const pointer = simulation.write_view();
            const startCopy = performance.now();
            new Uint8Array(buffer).set(new Uint8Array(memory.buffer, pointer, snapshotBytes));
            const endCopy = performance.now();
            if (measured) {
                snapshots.push(startCopy - startSnapshot);
                copies.push(endCopy - startCopy);
            }
            self.postMessage({
                kind: "view",
                tick,
                buffer,
                posted: performance.timeOrigin + endCopy,
            }, [buffer]);
        } else if (measured) {
            skipped++;
        }
        if (measured && performance.now() > deadline) missed++;

        if (finalTick) {
            self.postMessage({
                kind: "finish",
                report: {
                    trace: JSON.parse(simulation.finish()),
                    snapshot_bytes: snapshotBytes,
                    missed_deadlines: missed,
                    skipped_transfers: skipped,
                    step: timing(steps),
                    snapshot: timing(snapshots),
                    worker_copy: timing(copies),
                    worker_memory_bytes: memory.buffer.byteLength,
                },
            });
            simulation.free();
            return;
        }
        setTimeout(pacedFrame, Math.max(0, Math.ceil(deadline - performance.now())));
    }

    // Preserve the last complete view even when the page temporarily exhausts the pool.
    // Retry producing that view without running another simulation tick.
    function pacedFrame() {
        if (tick + 1 === options.ticks && recycle.length === 0) {
            setTimeout(pacedFrame, TICK_MS);
        } else {
            try { frame(); } catch (error) { reportError(error); }
        }
    }
    // Schedule through the guarded callback throughout the run.
    pacedFrame();
}
