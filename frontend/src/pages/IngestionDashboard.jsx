import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchIngestionStats,
  fetchIngestionJobs,
  ingestGoogleFormsData,
  ingestSlackData,
  uploadCsvFeedback,
  uploadIngestionDocument,
} from '../services/api';
import { showToast } from '../utils/toast';

const CARD = 'bg-white border border-slate-200 rounded-2xl shadow-sm';
const SNAPSHOT_KEY = 'ingestion_dashboard_snapshot_v1';
const EMPTY_OVERVIEW = {
  counts: {
    employees: 0,
    feedback: 0,
    meetings: 0,
    sentiment_insights: 0,
  },
};

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

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function normalizeOverview(raw) {
  const counts = raw?.counts || raw || {};
  return {
    ...EMPTY_OVERVIEW,
    ...raw,
    counts: {
      employees: toNumber(counts.employees),
      feedback: toNumber(counts.feedback),
      meetings: toNumber(counts.meetings),
      sentiment_insights: toNumber(counts.sentiment_insights ?? counts.insights),
    },
  };
}

function normalizeJobs(rawJobs) {
  if (!Array.isArray(rawJobs)) return [];
  return rawJobs.map((job) => ({
    ...job,
    records_processed: toNumber(job?.records_processed),
  }));
}

function readSnapshot() {
  try {
    const raw = localStorage.getItem(SNAPSHOT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return {
      overview: normalizeOverview(parsed?.overview),
      jobs: normalizeJobs(parsed?.jobs),
      savedAt: parsed?.savedAt || null,
    };
  } catch {
    return null;
  }
}

function writeSnapshot(overview, jobs) {
  try {
    localStorage.setItem(
      SNAPSHOT_KEY,
      JSON.stringify({
        overview: normalizeOverview(overview),
        jobs: normalizeJobs(jobs),
        savedAt: new Date().toISOString(),
      }),
    );
  } catch {
    // ignore localStorage failures
  }
}

export default function IngestionDashboard() {
  const [overview, setOverview] = useState(EMPTY_OVERVIEW);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('Live data synced from the database.');
  const [actionLoading, setActionLoading] = useState('');

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
      const [statsRes, jobsRes] = await Promise.all([fetchIngestionStats(), fetchIngestionJobs()]);
      const nextOverview = normalizeOverview(statsRes.data);
      const nextJobs = normalizeJobs(jobsRes.data);
      setOverview(nextOverview);
      setJobs(nextJobs);
      writeSnapshot(nextOverview, nextJobs);
      setStatus('Live data synced from the database.');
    } catch (error) {
      const snapshot = readSnapshot();
      if (snapshot) {
        setOverview(snapshot.overview);
        setJobs(snapshot.jobs);
        setStatus(`Showing latest available snapshot (${formatDate(snapshot.savedAt)}).`);
      } else {
        setOverview(EMPTY_OVERVIEW);
        setJobs([]);
        setStatus('No database snapshot available yet. Please refresh after data is ingested.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const queueAndRefresh = async (promiseFactory, successMessage, actionName) => {
    setActionLoading(actionName);
    setStatus('Submitting ingestion request...');
    try {
      await promiseFactory();
      setStatus(successMessage);
      await loadData();
    } catch (error) {
      setStatus('Request could not be completed. Please verify input and try again.');
    } finally {
      setActionLoading('');
    }
  };

  const handleCsvSubmit = async (e) => {
    e.preventDefault();
    if (!csvFile) {
      showToast('Please choose a CSV or Excel file first.', 'error', 2000);
      return;
    }
    await queueAndRefresh(() => uploadCsvFeedback(csvFile), 'CSV/Excel ingestion queued successfully.', 'csv');
  };

  const handleSlackSubmit = async (e) => {
    e.preventDefault();
    try {
      const messages = parseJsonArray(slackPayload);
      await queueAndRefresh(
        () => ingestSlackData({ channel: slackChannel, messages }),
        'Slack ingestion queued successfully.',
        'slack',
      );
    } catch (error) {
      showToast(error.message || 'Invalid Slack payload JSON.', 'error', 2000);
    }
  };

  const handleFormsSubmit = async (e) => {
    e.preventDefault();
    try {
      const responses = parseJsonArray(formsPayload);
      await queueAndRefresh(
        () => ingestGoogleFormsData({ form_id: formsId, responses }),
        'Google Forms ingestion queued successfully.',
        'forms',
      );
    } catch (error) {
      showToast(error.message || 'Invalid Google Forms payload JSON.', 'error', 2000);
    }
  };

  const handleDocumentSubmit = async (e) => {
    e.preventDefault();
    if (!docFile) {
      showToast('Please choose a document file first.', 'error', 2000);
      return;
    }
    await queueAndRefresh(
      () =>
        uploadIngestionDocument({
          file: docFile,
          participants,
        }),
      'Document ingestion queued successfully.',
      'document',
    );
  };

  return (
    <div className="space-y-6">
      <header className="rounded-2xl bg-gradient-to-r from-emerald-700 to-teal-600 text-white p-6 shadow-lg">
        <h1 className="text-2xl md:text-3xl font-bold">Unified Data Aggregation Engine</h1>
        <p className="mt-2 text-emerald-50">
          Ingest HRMS, CSV/Excel, Slack, Google Forms, and internal documents into one normalized pipeline.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {status ? <p className="text-sm bg-white/15 rounded-lg px-3 py-2 inline-block">{status}</p> : null}
          <button
            type="button"
            onClick={() => loadData()}
            className="text-sm bg-white text-emerald-700 hover:bg-emerald-50 rounded-lg px-3 py-2 font-medium"
          >
            Refresh Data
          </button>
        </div>
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
              <button
                type="submit"
                disabled={Boolean(actionLoading)}
                className="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {actionLoading === 'csv' ? 'Submitting...' : 'Queue CSV/Excel Ingestion'}
              </button>
            </form>

            <form onSubmit={handleDocumentSubmit} className={`${CARD} p-5 space-y-3`}>
              <h3 className="text-lg font-semibold text-slate-800">Document Connector</h3>
              <input
                type="file"
                accept=".txt,.pdf,.docx"
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
              <button
                type="submit"
                disabled={Boolean(actionLoading)}
                className="px-4 py-2 rounded-lg bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {actionLoading === 'document' ? 'Submitting...' : 'Queue Document Ingestion'}
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
              <button
                type="submit"
                disabled={Boolean(actionLoading)}
                className="px-4 py-2 rounded-lg bg-cyan-700 text-white hover:bg-cyan-800 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {actionLoading === 'slack' ? 'Submitting...' : 'Queue Slack Ingestion'}
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
              <button
                type="submit"
                disabled={Boolean(actionLoading)}
                className="px-4 py-2 rounded-lg bg-blue-700 text-white hover:bg-blue-800 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {actionLoading === 'forms' ? 'Submitting...' : 'Queue Forms Ingestion'}
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
