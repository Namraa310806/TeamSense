import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchIngestionJobs,
  fetchIngestionOverview,
  ingestGoogleFormsData,
  ingestSlackData,
  uploadCsvFeedback,
  uploadIngestionDocument,
} from '../services/api';

const CARD = 'bg-white border border-slate-200 rounded-2xl shadow-sm';

function formatDate(value) {
  if (!value) return 'N/A';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? 'N/A' : d.toLocaleString();
}

function parseJsonArray(jsonText) {
  if (!jsonText || !jsonText.trim()) return [];
  const parsed = JSON.parse(jsonText);
  if (!Array.isArray(parsed)) {
    throw new Error('Payload must be a JSON array.');
  }
  return parsed;
}

export default function IngestionDashboard() {
  const [overview, setOverview] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');

  const [csvFile, setCsvFile] = useState(null);
  const [docFile, setDocFile] = useState(null);
  const [participants, setParticipants] = useState('');
  const [slackChannel, setSlackChannel] = useState('hr-feedback');
  const [slackPayload, setSlackPayload] = useState(
    JSON.stringify(
      [
        {
          employee_email: 'alex@company.com',
          employee_name: 'Alex Parker',
          text: 'The onboarding process felt smooth and manager support is great.',
          timestamp: new Date().toISOString(),
        },
      ],
      null,
      2,
    ),
  );
  const [formsId, setFormsId] = useState('weekly-pulse-survey');
  const [formsPayload, setFormsPayload] = useState(
    JSON.stringify(
      [
        {
          employee_email: 'sam@company.com',
          name: 'Sam Lee',
          feedback: 'Need clearer priority alignment between teams.',
          timestamp: new Date().toISOString(),
        },
      ],
      null,
      2,
    ),
  );

  const architectureStages = useMemo(
    () => [
      {
        title: 'Stage 1 - Data Connectors',
        points: [
          'CSV / Excel Connector',
          'Slack Connector',
          'Google Forms Connector',
          'Document Connector',
        ],
      },
      {
        title: 'Stage 2 - Data Normalization',
        points: [
          'Employee Data: employee_id, name, department, manager, join_date',
          'Feedback Data: employee, source, sentiment, timestamp',
          'Meeting Data: participants, summary, sentiment',
        ],
      },
      {
        title: 'Stage 3 - Storage',
        points: ['Employee', 'Feedback', 'Meeting', 'Sentiment Insights'],
      },
      {
        title: 'Stage 4 - AI Processing',
        points: ['sentiment analysis', 'summarization', 'insight generation'],
      },
      {
        title: 'Stage 5 - Dashboard',
        points: ['employee profiles update automatically from normalized records'],
      },
    ],
    [],
  );

  const loadData = async () => {
    try {
      const [overviewRes, jobsRes] = await Promise.all([fetchIngestionOverview(), fetchIngestionJobs()]);
      setOverview(overviewRes.data);
      setJobs(jobsRes.data || []);
    } catch (error) {
      setStatus(error?.response?.data?.error || 'Failed to load ingestion dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const queueAndRefresh = async (promiseFactory, successMessage) => {
    setStatus('Queuing ingestion job...');
    try {
      await promiseFactory();
      setStatus(successMessage);
      await loadData();
    } catch (error) {
      setStatus(error?.response?.data?.error || 'Failed to queue ingestion job.');
    }
  };

  const handleCsvSubmit = async (e) => {
    e.preventDefault();
    if (!csvFile) {
      setStatus('Please choose a CSV or Excel file.');
      return;
    }
    await queueAndRefresh(() => uploadCsvFeedback(csvFile), 'CSV/Excel ingestion queued successfully.');
  };

  const handleSlackSubmit = async (e) => {
    e.preventDefault();
    try {
      const messages = parseJsonArray(slackPayload);
      await queueAndRefresh(
        () => ingestSlackData({ channel: slackChannel, messages }),
        'Slack ingestion queued successfully.',
      );
    } catch (error) {
      setStatus(error.message || 'Invalid Slack payload JSON.');
    }
  };

  const handleFormsSubmit = async (e) => {
    e.preventDefault();
    try {
      const responses = parseJsonArray(formsPayload);
      await queueAndRefresh(
        () => ingestGoogleFormsData({ form_id: formsId, responses }),
        'Google Forms ingestion queued successfully.',
      );
    } catch (error) {
      setStatus(error.message || 'Invalid Google Forms payload JSON.');
    }
  };

  const handleDocumentSubmit = async (e) => {
    e.preventDefault();
    if (!docFile) {
      setStatus('Please choose a meeting note document.');
      return;
    }
    await queueAndRefresh(
      () =>
        uploadIngestionDocument({
          file: docFile,
          participants,
        }),
      'Document ingestion queued successfully.',
    );
  };

  return (
    <div className="space-y-6">
      <header className="rounded-2xl bg-gradient-to-r from-emerald-700 to-teal-600 text-white p-6 shadow-lg">
        <h1 className="text-2xl md:text-3xl font-bold">Unified Data Aggregation Engine</h1>
        <p className="mt-2 text-emerald-50">
          Ingest HRMS, CSV/Excel, Slack, Google Forms, and internal documents into one normalized pipeline.
        </p>
        {status ? <p className="mt-3 text-sm bg-white/15 rounded-lg px-3 py-2 inline-block">{status}</p> : null}
      </header>

      {loading ? (
        <div className={`${CARD} p-6`}>
          <p className="text-slate-500">Loading ingestion overview...</p>
        </div>
      ) : (
        <>
          <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`${CARD} p-4`}>
              <p className="text-xs uppercase tracking-wide text-slate-500">Employees</p>
              <p className="text-2xl font-semibold text-slate-800">{overview?.counts?.employees || 0}</p>
            </div>
            <div className={`${CARD} p-4`}>
              <p className="text-xs uppercase tracking-wide text-slate-500">Feedback</p>
              <p className="text-2xl font-semibold text-slate-800">{overview?.counts?.feedback || 0}</p>
            </div>
            <div className={`${CARD} p-4`}>
              <p className="text-xs uppercase tracking-wide text-slate-500">Meetings</p>
              <p className="text-2xl font-semibold text-slate-800">{overview?.counts?.meetings || 0}</p>
            </div>
            <div className={`${CARD} p-4`}>
              <p className="text-xs uppercase tracking-wide text-slate-500">Sentiment Insights</p>
              <p className="text-2xl font-semibold text-slate-800">{overview?.counts?.sentiment_insights || 0}</p>
            </div>
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className={`${CARD} p-5`}>
              <h2 className="text-lg font-semibold text-slate-800 mb-3">Ingestion Architecture</h2>
              <div className="space-y-4">
                {architectureStages.map((stage) => (
                  <div key={stage.title} className="border border-slate-200 rounded-xl p-4 bg-slate-50">
                    <h3 className="font-semibold text-slate-700">{stage.title}</h3>
                    <ul className="mt-2 text-sm text-slate-600 list-disc list-inside space-y-1">
                      {stage.points.map((point) => (
                        <li key={point}>{point}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div className={`${CARD} p-5`}>
              <h2 className="text-lg font-semibold text-slate-800 mb-3">Normalized Internal Schema</h2>
              <div className="space-y-3 text-sm">
                <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
                  <p className="font-semibold text-slate-700">Employee Data</p>
                  <p className="text-slate-600">employee_id, name, department, manager, join_date</p>
                </div>
                <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
                  <p className="font-semibold text-slate-700">Feedback Data</p>
                  <p className="text-slate-600">employee, source, sentiment, timestamp</p>
                </div>
                <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
                  <p className="font-semibold text-slate-700">Meeting Data</p>
                  <p className="text-slate-600">participants, summary, sentiment</p>
                </div>
                <div className="rounded-xl border border-slate-200 p-3 bg-emerald-50 border-emerald-200">
                  <p className="font-semibold text-emerald-800">AI Pipeline</p>
                  <p className="text-emerald-700">
                    Every normalized record is sent to sentiment analysis, summarization, and insight generation.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <form onSubmit={handleCsvSubmit} className={`${CARD} p-5 space-y-3`}>
              <h3 className="text-lg font-semibold text-slate-800">CSV / Excel Connector</h3>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="w-full border border-slate-300 rounded-lg p-2"
              />
              <button type="submit" className="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700">
                Queue CSV/Excel Ingestion
              </button>
            </form>

            <form onSubmit={handleDocumentSubmit} className={`${CARD} p-5 space-y-3`}>
              <h3 className="text-lg font-semibold text-slate-800">Document Connector</h3>
              <input
                type="file"
                accept=".txt,.md,.pdf"
                onChange={(e) => setDocFile(e.target.files?.[0] || null)}
                className="w-full border border-slate-300 rounded-lg p-2"
              />
              <input
                type="text"
                value={participants}
                onChange={(e) => setParticipants(e.target.value)}
                placeholder="Participants (comma-separated)"
                className="w-full border border-slate-300 rounded-lg p-2"
              />
              <button type="submit" className="px-4 py-2 rounded-lg bg-teal-600 text-white hover:bg-teal-700">
                Queue Document Ingestion
              </button>
            </form>

            <form onSubmit={handleSlackSubmit} className={`${CARD} p-5 space-y-3`}>
              <h3 className="text-lg font-semibold text-slate-800">Slack Connector</h3>
              <input
                type="text"
                value={slackChannel}
                onChange={(e) => setSlackChannel(e.target.value)}
                placeholder="Channel name"
                className="w-full border border-slate-300 rounded-lg p-2"
              />
              <textarea
                value={slackPayload}
                onChange={(e) => setSlackPayload(e.target.value)}
                rows={8}
                className="w-full border border-slate-300 rounded-lg p-2 font-mono text-xs"
              />
              <button type="submit" className="px-4 py-2 rounded-lg bg-cyan-700 text-white hover:bg-cyan-800">
                Queue Slack Ingestion
              </button>
            </form>

            <form onSubmit={handleFormsSubmit} className={`${CARD} p-5 space-y-3`}>
              <h3 className="text-lg font-semibold text-slate-800">Google Forms Connector</h3>
              <input
                type="text"
                value={formsId}
                onChange={(e) => setFormsId(e.target.value)}
                placeholder="Form ID"
                className="w-full border border-slate-300 rounded-lg p-2"
              />
              <textarea
                value={formsPayload}
                onChange={(e) => setFormsPayload(e.target.value)}
                rows={8}
                className="w-full border border-slate-300 rounded-lg p-2 font-mono text-xs"
              />
              <button type="submit" className="px-4 py-2 rounded-lg bg-blue-700 text-white hover:bg-blue-800">
                Queue Forms Ingestion
              </button>
            </form>
          </section>

          <section className={`${CARD} p-5`}>
            <h2 className="text-lg font-semibold text-slate-800 mb-4">Async Pipeline Jobs (Celery)</h2>
            {jobs.length === 0 ? (
              <p className="text-slate-500 text-sm">No jobs queued yet.</p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500 border-b border-slate-200">
                      <th className="py-2 pr-4">Source</th>
                      <th className="py-2 pr-4">Status</th>
                      <th className="py-2 pr-4">Records</th>
                      <th className="py-2 pr-4">Created</th>
                      <th className="py-2 pr-4">Completed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <tr key={job.id} className="border-b border-slate-100 text-slate-700">
                        <td className="py-2 pr-4 uppercase">{job.source}</td>
                        <td className="py-2 pr-4">{job.status}</td>
                        <td className="py-2 pr-4">{job.records_processed}</td>
                        <td className="py-2 pr-4">{formatDate(job.created_at)}</td>
                        <td className="py-2 pr-4">{formatDate(job.completed_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
