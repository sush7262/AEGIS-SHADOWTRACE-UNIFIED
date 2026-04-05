# PROJECT AEGIS: Cyber-Infrastructure Defense Console

Welcome to **Project AEGIS**, a high-tech forensic dashboard designed to isolate and identify the "Shadow Controller" infiltrating Nexus City's infrastructure. 

This console bypasses deceptive JSON payloads and analyzes raw, live telemetry data, uncovering hidden HTTP DDoS attacks, cloned hardware serial numbers, and anomalous API latency spikes.

---

## Dashboard Interface
*A clean, modernized React SPA built for live forensic analysis.*

> **UI Features:** Dark graphite & slate-blue aesthetics, modular tabbed navigation, and interactive canvas visualizations to prevent data congestion.

---

## Key Features

* **Forensic City Map:** A visual `<canvas>` map rendering 500 infrastructure nodes. Nodes are dynamically colored based on their *true* underlying status (Clean, Infected, or Cloned), completely ignoring counterfeit "Operational" JSON labels.
* **The "Sleeper" Heatmap:** A real-time latency graph tracking API response times. It actively flags "Sleeper Nodes" that claim to be healthy but secretly cause >230ms rendering timeouts due to hidden malware execution.
* **Dynamic Schema Console:** A live forensics logger tracking the Shadow Controller's mid-session schema rotations (e.g., dynamically switching active columns from `load_val` to `L_V1` via cookie triggers).
* **Asset Registry:** An interactive data table that dynamically decodes Base64-masked `user_agent` strings into physical hardware Serial Numbers—exposing hidden machine cloning.
* **Attack Vector Analysis:** Real-time decoding of protocol vs. payload mismatches (uncovering HTTP 429 and HTTP 206 hijack codes).

---

## Tech Stack & Architecture

This project was recently migrated from a monolithic vanilla JS setup into a clean, decoupled **React** architecture.

* **Frontend:** React.js (Create React App)
* **Styling:** Custom Vanilla CSS (CSS Modules & Variables) utilizing a tactical Cyber-Defense color palette.
* **State & Logic:** A central `useAegisEngine.js` custom hook manages data aggregation, decoding Base64 strings, calculating latency stats, and tracking duplicates.
* **Backend Integration:** The React app uses Webpack proxying to seamlessly fetch dynamic datasets (`system_logs.csv`, `node_registry.csv`, `schema_config.csv`) from the root Python HTTP server.

## Scientific Concepts & Anomaly Detection Logic

AEGIS doesn't just look for static signatures; it uses mathematical and architectural concepts to identify the Shadow Controller’s footprints.

### 1. Hardware ID Cloning (Identity Spoofing)
* **Concept:** Frequency Analysis & Set Theory
* **Logic:** The defense console parses the `User-Agent` strings from the node registry, which contain Base64-masked identifiers. By decoding these strings (e.g., `U04tOTI4MA==` → `SN-9280`), AEGIS aggregates physical machine identities. If the cardinality of UUIDs mapped to a single Serial Number is greater than 1, it alerts for **Hardware Cloning** (a known evasion tactic where a single physical machine spins up multiple virtual nodes).
* **Equation:** `|{UUID ∈ Nodes | SN(UUID) = x}| > 1 ⇒ CLONE_DETECTED`

### 2. Sleeper Node Latency Spikes (Covert Cryptojacking)
* **Concept:** Time-Series Aggregation & Thresholding
* **Logic:** Malware often hides by mimicking clean health checks. AEGIS aggregates 10,000 live telemetry logs, mapping response times to specific nodes. If a node consistently claims to be `"OPERATIONAL"` but its average API latency ($\mu$) exceeds the normal operational threshold ($\tau = 230ms$), it is flagged as a "Sleeper". This indicates the node's CPU cycles are being covertly stolen by the Shadow Controller.
* **Equation:** `[Status == "OPERATIONAL"] ∧ [μ(Response_Time) > 230ms] ⇒ SLEEPER_NODE`

### 3. Protocol vs. Payload Mismatch (Layer 7 Evasion)
* **Concept:** Cross-Layer Validation (OSI Model)
* **Logic:** Deceptive endpoints often return clean Application Layer payloads (JSON: `{"status": "OPERATIONAL"}`) while the underlying HTTP Protocol reveals distress (e.g., `HTTP 429 Too Many Requests` or `HTTP 206 Partial Content`). AEGIS acts as a strict validator, overriding the JSON payload if the protocol layer violates expected norms.
* **Equation:** `if (JSON.status == OK) AND (HTTP.Code ∉ {200, 201}) ⇒ PAYLOAD_SPOOFED`

### 4. Temporal Schema Rotation Injections (TOCTOU)
* **Concept:** Time-of-Check to Time-of-Use (TOCTOU) Vulnerabilities
* **Logic:** The Shadow Controller attempts to bypass Web Application Firewalls (WAFs) by rotating the data schema mid-session based on time thresholds ($t=5000$) and HTTP Cookie triggers (`X-Schema-Ver`). AEGIS tracks this temporal rotation to lock down the exact moment the payload injection occurs.

---

---

## ShadowTrace AI Integration (Feature Module)

ShadowTrace AI is now integrated as an internal intelligent detection system. It reconstructs entity interactions, fingerprints metadata patterns, and surfaces probable hidden command nodes with explainable fusion scoring.

### Key Capabilities:
- **Graph Recomposition:** Builds interaction networks from raw API logs.
- **Explainable Attribution:** Assigns confidence scores based on behavioral anomalies.
- **Intelligent Ingestion:** Automatically watches `./ingest_drop` for new log files.
- **Interactive Dashboard:** Dedicated "Attack Intelligence Dashboard" for deep forensics.

---

## Local Setup & Execution

### 1. Unified Backend (AEGIS + ShadowTrace)
The new backend handles both legacy CSV telemetry and modern ShadowTrace AI endpoints.

```bash
# From the root directory (TEAM-HAPPY_AEGIS)
# Install dependencies
pip install -r requirements.txt

# Start the unified FastAPI server
python backend/main.py
```
This server runs on port 8000. It serves:
- `http://localhost:8000/*.csv` (AEGIS Core)
- `http://localhost:8000/api/shadowtrace/*` (ShadowTrace AI)

### 2. Live Console (React)
Run the React application locally.
```bash
# In a new terminal window
cd aegis-app
npm install
npm start
```

The unified console will open at `http://localhost:3000`. ShadowTrace can be accessed via the **⚔ ShadowTrace AI** tab in the sidebar.

---

## The Mission
Nexus City relies on Project AEGIS. Do not trust the JSON payloads. Verify the protocols. Hunt the anomalies. Good luck.
