import React, { useState } from 'react';
import api from '../services/api';

const IngestionDashboard = () => {
  const [csvFile, setCsvFile] = useState(null);
  const [status, setStatus] = useState('');

  const handleCsvUpload = async (e) => {
    e.preventDefault();
    if (!csvFile) return;
    const formData = new FormData();
    formData.append('file', csvFile);

    try {
      const response = await api.post('/api/ingestion/upload-csv/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setStatus(`Queued: ${response.data.file}`);
    } catch (error) {
      setStatus('Upload failed');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Data Ingestion</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">CSV/Excel</h2>
          <form onSubmit={handleCsvUpload}>
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={(e) => setCsvFile(e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-4"
            />
            <button type="submit" className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
              Upload & Process
            </button>
          </form>
          <p className="mt-2 text-sm text-gray-600">{status}</p>
        </div>
        {/* Slack, Forms, Docs tabs TODO */}
        <div className="bg-gray-50 p-6 rounded-lg shadow col-span-full">
          <h3>Status: Pipeline ready. Check /api/ingestion/feedback/ for data.</h3>
        </div>
      </div>
    </div>
  );
};

export default IngestionDashboard;

