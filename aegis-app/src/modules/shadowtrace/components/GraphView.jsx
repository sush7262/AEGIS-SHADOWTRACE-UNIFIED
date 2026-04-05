import { useEffect, useRef } from "react";
import * as d3 from "d3";

/**
 * D3 force-directed graph: sources (ip:*) vs services (svc:*).
 */
export function GraphView({ graph, selectedId, onSelectNode }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    if (!graph?.nodes?.length) {
      d3.select(el).selectAll("*").remove();
      return;
    }

    d3.select(el).selectAll("*").remove();

    const width = el.clientWidth || 800;
    const height = el.clientHeight || 520;

    const svg = d3
      .select(el)
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("class", "block");

    const gRoot = svg.append("g");

    const zoom = d3
      .zoom()
      .scaleExtent([0.35, 4])
      .on("zoom", (ev) => {
        gRoot.attr("transform", ev.transform);
      });
    svg.call(zoom);

    const nodes = graph.nodes.map((d) => ({ ...d }));
    const links = graph.edges.map((d) => ({ ...d }));

    const link = gRoot
      .append("g")
      .attr("stroke", "#243352")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-opacity", 0.85)
      .attr("stroke-width", (d) => Math.min(10, 0.8 + Math.sqrt(d.weight || 1)));

    const drag = d3
      .drag()
      .on("start", (ev, d) => {
        if (!ev.active) simulation.alphaTarget(0.25).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (ev, d) => {
        d.fx = ev.x;
        d.fy = ev.y;
      })
      .on("end", (ev, d) => {
        if (!ev.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    const node = gRoot
      .append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (d) => (d.type === "source" ? 11 : 8))
      .attr("stroke-width", (d) => (d.id === selectedId ? 3 : 2))
      .attr("stroke", (d) => {
        if (d.id === selectedId) return "#00f0ff";
        if (d.is_suspicious) return "#ff3366";
        return "#00f0ff44";
      })
      .attr("fill", (d) => {
        if (d.is_suspicious) return "rgba(255,51,102,0.55)";
        if (d.type === "service") return "#152238";
        return "#0b1f38";
      })
      .style("cursor", "pointer")
      .call(drag)
      .on("click", (ev, d) => {
        ev.stopPropagation();
        onSelectNode?.(d);
      });

    node
      .append("title")
      .text((d) => {
        const m = d.metadata || {};
        const bits = [
          d.label,
          `entity: ${d.type}`,
          `requests: ${d.total_requests}`,
          `deg_c: ${m.degree_centrality ?? "—"}`,
          `between: ${m.betweenness ?? "—"}`,
          `suspicious: ${d.is_suspicious ? "yes" : "no"}`,
        ];
        if (d.fingerprint_id) bits.push(`fp: ${d.fingerprint_id}`);
        return bits.join("\n");
      });

    const labels = gRoot
      .append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .text((d) => {
        const t = String(d.label || "");
        return t.length > 20 ? `${t.slice(0, 18)}…` : t;
      })
      .attr("font-size", 9)
      .attr("fill", "#8fa3c4")
      .attr("dx", 14)
      .attr("dy", 4)
      .style("pointer-events", "none");

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance((l) => 70 + Math.sqrt((l.weight || 1) * 2))
          .strength(0.45)
      )
      .force("charge", d3.forceManyBody().strength(-280))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d) => (d.type === "source" ? 22 : 16)));

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
      labels.attr("x", (d) => d.x).attr("y", (d) => d.y);
    });

    return () => simulation.stop();
  }, [graph, selectedId, onSelectNode]);

  return (
    <div
      ref={containerRef}
      className="relative h-[min(56vh,560px)] w-full min-h-[320px] rounded-lg border border-cyber-border bg-[#050810] overflow-hidden scanline"
    />
  );
}
