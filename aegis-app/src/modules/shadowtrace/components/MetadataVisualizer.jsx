import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const axisStyle = { fill: "#6b7a99", fontSize: 11 };
const gridStyle = { stroke: "#1e2a45" };
const tipStyle = {
  backgroundColor: "#0d1424",
  border: "1px solid #1e2a45",
  borderRadius: 8,
  fontSize: 12,
};

function toBarData(dict, limit = 12) {
  if (!dict || typeof dict !== "object") return [];
  return Object.entries(dict)
    .slice(0, limit)
    .map(([name, value]) => ({ name: name.replace(/^ip:/, ""), value }));
}

export function MetadataVisualizer({ charts, timeline, benignVs, highlightBucket }) {
  const freq = toBarData(charts?.request_frequency);
  const interval = toBarData(charts?.interval_consistency);
  const header = toBarData(charts?.header_concentration);
  const lineData = (timeline || []).map((t, i) => ({
    i,
    bucket: new Date(t.bucket).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    requests: t.requests,
    nodes: t.unique_sources,
  }));
  const hiX =
    highlightBucket != null && lineData[highlightBucket] ? lineData[highlightBucket].bucket : null;

  const compare = benignVs
    ? [
        { name: "interval_consistency", benign: benignVs.benign_sample?.avg_interval_consistency ?? 0, sus: benignVs.suspicious?.avg_interval_consistency ?? 0 },
        { name: "header_focus", benign: benignVs.benign_sample?.avg_header_concentration ?? 0, sus: benignVs.suspicious?.avg_header_concentration ?? 0 },
        { name: "endpoint_hhi", benign: benignVs.benign_sample?.avg_endpoint_hhi ?? 0, sus: benignVs.suspicious?.avg_endpoint_hhi ?? 0 },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="grid xl:grid-cols-2 gap-6">
        <div className="glass-panel p-4">
          <h4 className="text-sm font-display text-cyber-accent mb-3">Request volume timeline</h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStyle.stroke} />
                <XAxis dataKey="bucket" tick={axisStyle} interval="preserveStartEnd" minTickGap={24} />
                <YAxis tick={axisStyle} />
                <Tooltip contentStyle={tipStyle} />
                <Legend />
                <Line type="monotone" dataKey="requests" stroke="#00f0ff" strokeWidth={2} dot={false} name="Requests" />
                <Line type="monotone" dataKey="nodes" stroke="#ffaa00" strokeWidth={1.5} dot={false} name="Unique sources" />
                {hiX ? <ReferenceLine x={hiX} stroke="#ff3366" strokeDasharray="4 4" /> : null}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel p-4">
          <h4 className="text-sm font-display text-cyber-accent mb-3">Benign vs suspicious (aggregate)</h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compare}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStyle.stroke} />
                <XAxis dataKey="name" tick={axisStyle} />
                <YAxis tick={axisStyle} domain={[0, 1]} />
                <Tooltip contentStyle={tipStyle} />
                <Legend />
                <Bar dataKey="benign" fill="#3b82f6aa" name="Benign sample" />
                <Bar dataKey="sus" fill="#ff3366cc" name="Suspicious cohort" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {[
          { title: "Request frequency (top sources)", data: freq, fill: "#00f0ff" },
          { title: "Interval consistency", data: interval, fill: "#a855f7" },
          { title: "Header ordering concentration", data: header, fill: "#f97316" },
        ].map((c) => (
          <div key={c.title} className="glass-panel p-4">
            <h4 className="text-xs font-display text-cyber-accent mb-2">{c.title}</h4>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={c.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStyle.stroke} />
                  <XAxis dataKey="name" tick={axisStyle} hide />
                  <YAxis tick={axisStyle} />
                  <Tooltip contentStyle={tipStyle} />
                  <Bar dataKey="value" fill={c.fill} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
