const BATCHES = 128;
const CHANNEL = "terminal-command-bench-v1";
const token = location.hash.slice(1);
const status = document.querySelector("#status");
const encode = new TextEncoder();

async function api(path, body) {
    const response = await fetch(path, {
        method: body ? "POST" : "GET",
        cache: "no-store",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) throw new Error(`Signaling returned ${response.status}. ${await response.text()}`);
    if (response.status !== 204) return response.json();
}

function batch(player, index) {
    return {
        version: 1,
        tick: 1 + index * 4,
        player,
        advance: index % 3 !== player,
        lane_mm: (index * 127 + player * 759) % 12001 - 6000,
    };
}

function gather(peer, relay) {
    return new Promise((resolve, reject) => {
        const eligible = relay ? / typ relay(?: |\r?$)/m : / typ (?:host|srflx|prflx)(?: |\r?$)/m;
        let settleTimer;
        const deadline = setTimeout(finish, 18000);

        function finish() {
            clearTimeout(deadline);
            clearTimeout(settleTimer);
            peer.removeEventListener("icecandidate", candidate);
            peer.removeEventListener("icegatheringstatechange", gathering);
            if (eligible.test(peer.localDescription?.sdp ?? "")) resolve();
            else reject(new Error(`Browser ICE gathered no ${relay ? "relay" : "direct"} candidates.`));
        }
        function candidate({ candidate }) {
            // Some STUN/TURN routes take much longer to fail than a usable candidate takes to arrive.
            if (!settleTimer && candidate?.type === (relay ? "relay" : "srflx")) {
                settleTimer = setTimeout(finish, 1200);
            }
        }
        function gathering() {
            if (peer.iceGatheringState === "complete") finish();
        }
        peer.addEventListener("icecandidate", candidate);
        peer.addEventListener("icegatheringstatechange", gathering);
        if (relay && eligible.test(peer.localDescription?.sdp ?? "")) {
            settleTimer = setTimeout(finish, 1200);
        }
        gathering();
    });
}

function exchange(channel) {
    return new Promise((resolve, reject) => {
        let inbound_bytes = 0;
        let outbound_bytes = 0;
        let index = 0;
        let opened;
        const timer = setTimeout(() => reject(new Error("Data channel exchange timed out.")), 35000);
        channel.onopen = () => {
            opened = performance.now();
            status.textContent = "Exchanging ordered command batches…";
        };
        channel.onerror = () => { clearTimeout(timer); reject(new Error("Data channel error.")); };
        channel.onclose = () => { clearTimeout(timer); reject(new Error("Data channel closed.")); };
        channel.onmessage = ({ data }) => {
            try {
                if (data === "batches-verified" && index === BATCHES) {
                    clearTimeout(timer);
                    resolve({ inbound_bytes, outbound_bytes, batches: index, opened });
                    return;
                }
                const inbound = JSON.parse(data);
                const expected = batch(0, index);
                if (index >= BATCHES || Object.keys(expected).some((key) => expected[key] !== inbound[key])) {
                    throw new Error(`Invalid native batch at index ${index}.`);
                }
                const reply = JSON.stringify(batch(1, index++));
                inbound_bytes += encode.encode(data).length;
                outbound_bytes += encode.encode(reply).length;
                channel.send(reply);
            } catch (error) {
                clearTimeout(timer);
                reject(error);
            }
        };
    });
}

async function run() {
    if (!/^[0-9a-f]{48}$/.test(token)) throw new Error("Open the complete session URL printed by tc-rtc.");
    const config = await api("./api/config");
    const peer = new RTCPeerConnection(config);
    try {
        const started = performance.now();
        const channel = peer.createDataChannel(CHANNEL, { ordered: true });
        await peer.setLocalDescription(await peer.createOffer());
        await gather(peer, config.iceTransportPolicy === "relay");
        const batches = exchange(channel);
        // Reserve the rejection for the awaited exchange while the answer travels via signaling.
        batches.catch(() => {});
        const answer = await api("./api/offer", peer.localDescription);
        await peer.setRemoteDescription(answer);
        const { opened, ...counts } = await batches;

        const stats = await peer.getStats();
        const transport = [...stats.values()].find((item) =>
            item.type === "transport" && item.selectedCandidatePairId);
        const pair = stats.get(transport?.selectedCandidatePairId);
        if (!pair) throw new Error("Browser provided no selected ICE candidate pair.");
        const local = stats.get(pair.localCandidateId);
        const remote = stats.get(pair.remoteCandidateId);
        const report = {
            ...counts,
            browser: navigator.userAgent,
            local_candidate: local.candidateType,
            remote_candidate: remote.candidateType,
            protocol: local.protocol,
            connection_ms: opened - started,
            ice_rtt_ms: pair.currentRoundTripTime === undefined ? null : pair.currentRoundTripTime * 1000,
        };
        await api("./api/confirm", report);
        return report;
    } finally {
        peer.close();
    }
}

run().then((report) => {
    window.terminalCommandRtcReport = report;
    status.textContent = `Verified ${report.batches} ordered batches in each direction over ${report.local_candidate} / ${report.remote_candidate} ICE.`;
    document.querySelector("#result").textContent = JSON.stringify(report, null, 2);
}).catch((error) => {
    window.terminalCommandRtcError = String(error);
    status.textContent = String(error);
}).finally(() => {
    status.dataset.complete = "true";
});
