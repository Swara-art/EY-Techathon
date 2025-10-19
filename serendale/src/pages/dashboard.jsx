import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import "../App.css";

export default function Dashboard() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
  const location = useLocation();
  const stem = location.state?.upload
    ? (location.state.upload.filename || "").replace(/\.[^.]+$/, "")
    : null;

  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setErr("");
        const url = stem
          ? `${API_BASE}/ingest/data?stem=${encodeURIComponent(stem)}`
          : `${API_BASE}/ingest/data`;
        const res = await fetch(url, { headers: { Accept: "application/json" } });
        const json = await res.json();
        if (!res.ok) throw new Error(json?.detail || res.statusText);
        setColumns(json.columns || []);
        setRows(json.rows || []);
      } catch (e) {
        setErr(e.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    })();
  }, [API_BASE, stem]);

  const downloadUrl = stem
    ? `${API_BASE}/ingest/download?stem=${encodeURIComponent(stem)}`
    : `${API_BASE}/ingest/download`;

  return (
    <div className="dashboard-container">
      <div className="container">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h1 className="dashboard-title">Validated Provider Data</h1>
          <a href={downloadUrl} className="pill-btn">
            <span className="pill-text">Download Updated CSV</span>
          </a>
        </div>

        {err && <p style={{ color: "red" }}>{err}</p>}
        {loading && <p>Loading...</p>}

        {!loading && !err && (
          <div className="table-wrapper" style={{ overflowX: "auto", marginTop: 16 }}>
            <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {columns.map((col) => (
                    <th key={col} style={th}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length} style={{ textAlign: "center", color: "#9ca3af" }}>
                      No data found.
                    </td>
                  </tr>
                ) : (
                  rows.map((row, idx) => (
                    <tr key={idx}>
                      {columns.map((col) => (
                        <td key={col} style={td}>{String(row[col] ?? "")}</td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

const th = {
  textAlign: "left",
  borderBottom: "1px solid #333",
  padding: "8px 6px",
  fontWeight: 600,
  whiteSpace: "nowrap",
};
const td = {
  borderBottom: "1px dotted #333",
  padding: "8px 6px",
  whiteSpace: "nowrap",
};
