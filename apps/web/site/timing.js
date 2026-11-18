export function timing(samples) {
    if (!samples.length) {
        return { samples: 0, mean_ms: 0, p50_ms: 0, p95_ms: 0, p99_ms: 0, max_ms: 0 };
    }
    samples.sort((a, b) => a - b);
    const count = samples.length;
    const percentile = (p) => samples[Math.ceil(count * p) - 1];
    return {
        samples: count,
        mean_ms: samples.reduce((sum, sample) => sum + sample, 0) / count,
        p50_ms: percentile(0.50),
        p95_ms: percentile(0.95),
        p99_ms: percentile(0.99),
        max_ms: samples[count - 1],
    };
}
