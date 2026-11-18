import { timing } from "./timing.js";

const params = new URLSearchParams(location.search);
const mode = params.get("mode") ?? "battle";
const options = {
    units: number("units", 500),
    rigs: number("rigs", 0),
    seed: number("seed", 21041),
    ticks: number("ticks", mode === "battle" || mode === "replay" ? 400 : 0),
    warmup: number("warmup", mode === "replay" ? 0 : 60),
    width: number("width", 1920),
    height: number("height", 1080),
    inspect: mode === "inspect",
};
const status = document.querySelector("#status");
const download = document.querySelector("#download");
let worker;
let renderer;
let rendererMemory;

function number(key, fallback) {
    return params.has(key) ? Number(params.get(key)) : fallback;
}

function fail(error) {
    worker?.terminate();
    window.terminalCommandError = String(error);
    status.textContent = String(error);
    console.error(error);
}

function done(report) {
    window.terminalCommandReport = report;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    download.href = URL.createObjectURL(blob);
    download.hidden = false;
    status.textContent = report.frame
        ? `Complete · ${report.mean_frames_per_second.toFixed(1)} mean FPS · p95 frame ${report.frame.p95_ms.toFixed(1)} ms`
        : `Complete · ${report.trace.hashes.length} state hashes`;
}

function startWorker(headless) {
    const handoff = [];
    const pageCopy = [];
    let pageSkipped = 0;
    worker = new Worker(new URL("./simulation-worker.js", import.meta.url), { type: "module" });
    worker.onerror = (event) => fail(event.message);
    worker.onmessage = ({ data }) => {
        try {
            switch (data.kind) {
                case "view": {
                    const received = performance.now();
                    const accepted = renderer.push_view(data.tick, new Uint8Array(data.buffer));
                    const copied = performance.now();
                    worker.postMessage({ kind: "recycle", buffer: data.buffer }, [data.buffer]);
                    if (options.ticks && data.tick > options.warmup) {
                        handoff.push(Math.max(0, performance.timeOrigin - data.posted + received));
                        if (accepted) pageCopy.push(copied - received);
                        else pageSkipped++;
                    }
                    break;
                }
                case "finish":
                    renderer.finish(JSON.stringify(data.report));
                    worker.terminate();
                    waitForRenderer({
                        user_agent: navigator.userAgent,
                        worker_delivery: timing(handoff),
                        page_copy: timing(pageCopy),
                        page_skipped: pageSkipped,
                    });
                    break;
                case "headless":
                    done(data.report);
                    worker.terminate();
                    break;
                case "error":
                    fail(data.message);
                    break;
            }
        } catch (error) {
            fail(error);
        }
    };
    worker.postMessage({ kind: "start", options, headless });
}

function waitForRenderer(browser) {
    const started = performance.now();
    const timer = setInterval(() => {
        const report = renderer.report();
        if (report) {
            clearInterval(timer);
            done({ ...JSON.parse(report), browser: {
                ...browser, ...window.terminalCommandGpu, renderer_memory_bytes: rendererMemory.buffer.byteLength,
            } });
        } else if (performance.now() - started > 10000) {
            clearInterval(timer);
            fail("The renderer did not finish consuming the simulation views.");
        }
    }, 50);
}

async function run() {
    if (!["battle", "replay", "inspect"].includes(mode)
        || !Object.entries(options).every(([key, value]) => key === "inspect" || (Number.isInteger(value) && value >= 0))
        || ![500, 4000].includes(options.units) || options.rigs > options.units || options.rigs % 2
        || options.ticks > 100000 || (options.ticks && options.warmup >= options.ticks)
        || (mode === "replay" && options.ticks === 0) || options.seed > 0xffffffff
        || options.width < 320 || options.width > 3840 || options.height < 240 || options.height > 2160) {
        throw new Error("Invalid benchmark options. Check units, rigs, seed, ticks, warmup and resolution.");
    }
    const form = document.querySelector("#settings");
    form.elements.units.value = String(options.units);
    const rigs = form.elements.rigs;
    if (![...rigs.options].some((option) => Number(option.value) === options.rigs)) {
        rigs.add(new Option(String(options.rigs)));
    }
    rigs.value = String(options.rigs);

    if (mode === "replay") {
        status.textContent = "Running the headless replay in a Web Worker…";
        startWorker(true);
        return;
    }

    const adapter = await navigator.gpu?.requestAdapter({ powerPreference: "high-performance" });
    if (!adapter) {
        throw new Error("This browser could not open a WebGPU adapter. Try a desktop browser with WebGPU and hardware acceleration enabled.");
    }
    const info = adapter.info;
    const device = await adapter.requestDevice();
    window.terminalCommandGpu = {
        gpu: { vendor: info.vendor, architecture: info.architecture, device: info.device, description: info.description, fallback: info.isFallbackAdapter },
    };
    device.destroy();

    renderer = await import("./pkg/client.js");
    rendererMemory = (await renderer.default()).memory;
    try {
        renderer.start(JSON.stringify(options));
    } catch (error) {
        // winit uses an exception to hand control to the browser event loop.
        if (!String(error).includes("Using exceptions for control flow")) throw error;
    }

    if (options.inspect) {
        form.hidden = true;
        const clips = document.querySelector("#clips");
        clips.hidden = false;
        clips.addEventListener("click", ({ target }) => {
            if (target.dataset.clip !== undefined) renderer.select_clip(Number(target.dataset.clip));
        });
    }
    status.textContent = options.inspect ? "Loading the Rivet rig…" : "Preparing the battlefield…";
    const loadingStarted = performance.now();
    const timer = setInterval(() => {
        const state = JSON.parse(renderer.status());
        window.terminalCommandStatus = state;
        if (state.error) {
            clearInterval(timer);
            fail(state.error);
        } else if (!state.ready && performance.now() - loadingStarted > 60000) {
            clearInterval(timer);
            fail("The WebGPU battlefield did not initialize. Check hardware acceleration and the browser console.");
        } else if (state.ready && options.inspect) {
            status.textContent = `Rivet · ${["Idle", "Move", "Fire"][state.clip]} · Cyan / Ember`;
            if (state.pose_changes.every((count) => count >= 8) && !window.terminalCommandRigVerified) {
                window.terminalCommandRigVerified = { ...state, ...window.terminalCommandGpu };
            }
        } else if (state.ready && !worker) {
            startWorker(false);
            status.textContent = `Running ${options.units.toLocaleString()} units · ${options.rigs} Rivet rigs`;
            clearInterval(timer);
        }
    }, 100);
}

run().catch(fail);
