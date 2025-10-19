import React, { useState, useEffect } from "react";
import '../App.css';

export default function Dashboard() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch data from backend API
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:5000/api/data");
      const json = await response.json();
      setData(json.data || []);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="dashboard-container">
      <div className="container">
        <h1 className="dashboard-title">Data Records</h1>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>NPI</th>
                <th>Full Name</th>
                <th>Speciality Action</th>
                <th>License Action</th>
                <th>Anomaly Flag</th>
                <th>Row Action</th>
                <th>Priority Score</th>
              </tr>
            </thead>
            <tbody>
              {data.length === 0 && !loading &&
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: '#9ca3af' }}>No data found.</td>
                </tr>
              }
              {data.map((item, idx) => (
                <tr key={idx}>
                  <td>{item["NPI"]}</td>
                  <td>{item["Full Name"]}</td>
                  <td>{item["Speciality Action"]}</td>
                  <td>{item["License Action"]}</td>
                  <td>{item["Anomaly Flag"]}</td>
                  <td>{item["Row Action"]}</td>
                  <td>{item["Priority Score"]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {loading && <p className="no-more-text">Loading...</p>}
      </div>
    </div>
  );
}
