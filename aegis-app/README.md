# 🛡️ PROJECT AEGIS: Cyber-Infrastructure Defense Console

Welcome to **Project AEGIS**, a high-tech forensic dashboard designed to isolate and identify the "Shadow Controller" infiltrating Nexus City's infrastructure. 

This console bypasses deceptive JSON payloads and analyzes raw, live telemetry data, uncovering hidden HTTP DDoS attacks, cloned hardware serial numbers, and anomalous API latency spikes.

---

## 📸 Dashboard Interface
*A clean, modernized React SPA built for live forensic analysis.*

> **UI Features:** Dark graphite & slate-blue aesthetics, modular tabbed navigation, and interactive canvas visualizations to prevent data congestion.

---

## 🚀 Key Features

* **⬡ Forensic City Map:** A visual `<canvas>` map rendering 500 infrastructure nodes. Nodes are dynamically colored based on their *true* underlying status (Clean, Infected, or Cloned), completely ignoring counterfeit "Operational" JSON labels.
* **◈ The "Sleeper" Heatmap:** A real-time latency graph tracking API response times. It actively flags "Sleeper Nodes" that claim to be healthy but secretly cause >230ms rendering timeouts due to hidden malware execution.
* **⟨/⟩ Dynamic Schema Console:** A live forensics logger tracking the Shadow Controller's mid-session schema rotations (e.g., dynamically switching active columns from `load_val` to `L_V1` via cookie triggers).
* **▦ Asset Registry:** An interactive data table that dynamically decodes Base64-masked `user_agent` strings into physical hardware Serial Numbers—exposing hidden machine cloning.
* **⚡ Attack Vector Analysis:** Real-time decoding of protocol vs. payload mismatches (uncovering HTTP 429 and HTTP 206 hijack codes).

---

## 🛠️ Tech Stack & Architecture

This project was recently migrated from a monolithic vanilla JS setup into a clean, decoupled **React** architecture.

* **Frontend:** React.js (Create React App)
* **Styling:** Custom Vanilla CSS (CSS Modules & Variables) utilizing a tactical Cyber-Defense color palette.
* **State & Logic:** A central `useAegisEngine.js` custom hook manages data aggregation, decoding Base64 strings, calculating latency stats, and tracking duplicates.
* **Backend Integration:** The React app uses Webpack proxying to seamlessly fetch dynamic datasets (`system_logs.csv`, `node_registry.csv`, `schema_config.csv`) from the root Python HTTP server.

---

## ⚙️ Local Setup & Execution

Because the dashboard fetches live CSV telemetry dynamically, you need to run both the static file server and the React frontend.

### 1. Start the Data Server
This serves the raw `.csv` datasets to the frontend.
```bash
# From the root directory (TEAM-HAPPY_AEGIS)
python -m http.server 8000
```

### 2. Start the AEGIS Console
Run the React application locally.
```bash
# In a new terminal window
cd aegis-app
npm install
npm start
```

The console will automatically open at `http://localhost:3000` and proxy its data requests to the Python server on port 8000.

---

## 🕵️‍♂️ The Mission
Nexus City relies on Project AEGIS. Do not trust the JSON payloads. Verify the protocols. Hunt the anomalies. Good luck.
