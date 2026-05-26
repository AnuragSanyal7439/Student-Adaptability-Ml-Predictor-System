import {
  Activity,
  AlertCircle,
  BarChart3,
  Brain,
  CheckCircle2,
  Database,
  Download,
  FileText,
  Gauge,
  Home,
  Info,
  Loader2,
  RefreshCw,
  Upload,
} from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';

type FeatureDefinition = {
  name: string;
  type: 'categorical';
  options: string[];
};

type FeatureInfoResponse = {
  features: FeatureDefinition[];
  feature_order: string[];
  target: string;
  target_options: string[];
};

type PredictionResponse = {
  status: string;
  prediction: string;
  confidence: number;
  probabilities: Record<string, number>;
  timestamp: string;
};

type ModelScore = {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
};

type ClassificationReportEntry = {
  precision: number;
  recall: number;
  'f1-score': number;
  support: number;
};

type MetricsResponse = {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  selected_model_name: string;
  model_comparison: Record<string, ModelScore>;
  confusion_matrix: number[][];
  classification_report: Record<string, ClassificationReportEntry | number>;
  class_labels: string[];
  train_samples: number;
  test_samples: number;
  total_samples: number;
};

type HealthResponse = {
  status: string;
  service: string;
  model_available: boolean;
  model_loaded: boolean;
  metrics_available: boolean;
  timestamp: string;
};

type SectionId = 'dashboard' | 'predict' | 'batch' | 'metrics' | 'about';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

const sections: Array<{ id: SectionId; label: string; icon: typeof Home }> = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'predict', label: 'Predict', icon: Brain },
  { id: 'batch', label: 'Batch CSV', icon: Upload },
  { id: 'metrics', label: 'Metrics', icon: BarChart3 },
  { id: 'about', label: 'About', icon: Info },
];

const sampleDefaults: Record<string, string> = {
  Gender: 'Boy',
  Age: '21-25',
  'Education Level': 'University',
  'Institution Type': 'Government',
  'IT Student': 'Yes',
  Location: 'Yes',
  'Load-shedding': 'Low',
  'Financial Condition': 'Mid',
  'Internet Type': 'Wifi',
  'Network Type': '4G',
  'Class Duration': '1-3',
  'Self Lms': 'Yes',
  Device: 'Computer',
};

function classNames(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ');
}

function apiUrl(path: string) {
  return `${API_BASE}${path}`;
}

async function getApiError(response: Response) {
  try {
    const data = (await response.json()) as { error?: string; details?: unknown };
    if (Array.isArray(data.details) && data.details.length > 0) {
      const firstDetail = data.details[0] as { field?: string; message?: string };
      const fieldPrefix = firstDetail.field ? `${firstDetail.field}: ` : '';
      return `${data.error ?? 'Request failed'} (${fieldPrefix}${firstDetail.message ?? 'see details'})`;
    }
    return data.error ?? response.statusText;
  } catch {
    return response.statusText || 'Request failed';
  }
}

function getDownloadFilename(response: Response, fallback: string) {
  const disposition = response.headers.get('content-disposition');
  const match = disposition?.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/i);
  return match?.[1] ? decodeURIComponent(match[1]) : fallback;
}

function downloadBlob(blob: Blob, filename: string, keepUrl = false) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  if (!keepUrl) {
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return url;
}

function PercentBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="font-medium text-slate-700">{label}</span>
        <span className="tabular-nums text-slate-600">{value.toFixed(2)}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-200">
        <div
          className="h-2 rounded-full bg-teal-600"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  );
}

function StatTile({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string;
  icon: typeof Activity;
  tone: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
        </div>
        <div className={classNames('rounded-md p-2 text-white', tone)}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

function App() {
  const [activeSection, setActiveSection] = useState<SectionId>('dashboard');
  const [featureInfo, setFeatureInfo] = useState<FeatureInfoResponse | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [featureError, setFeatureError] = useState('');
  const [predictionError, setPredictionError] = useState('');
  const [pdfMessage, setPdfMessage] = useState('');
  const [pdfDownload, setPdfDownload] = useState<{ url: string; filename: string } | null>(null);
  const [metricsError, setMetricsError] = useState('');
  const [batchMessage, setBatchMessage] = useState('');
  const [batchError, setBatchError] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [isUploadingBatch, setIsUploadingBatch] = useState(false);
  const [isRefreshingMetrics, setIsRefreshingMetrics] = useState(false);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [healthResponse, featureResponse, metricsResponse] = await Promise.all([
          fetch(apiUrl('/api/health')),
          fetch(apiUrl('/api/feature-info')),
          fetch(apiUrl('/api/metrics')),
        ]);

        if (healthResponse.ok) {
          setHealth((await healthResponse.json()) as HealthResponse);
        }

        if (!featureResponse.ok) {
          throw new Error(await getApiError(featureResponse));
        }
        const featurePayload = (await featureResponse.json()) as FeatureInfoResponse;
        setFeatureInfo(featurePayload);

        const defaults = featurePayload.features.reduce<Record<string, string>>((acc, feature) => {
          acc[feature.name] = sampleDefaults[feature.name] ?? feature.options[0] ?? '';
          return acc;
        }, {});
        setFormData(defaults);

        if (metricsResponse.ok) {
          setMetrics((await metricsResponse.json()) as MetricsResponse);
          setMetricsError('');
        } else {
          setMetricsError(await getApiError(metricsResponse));
        }
      } catch (error) {
        setFeatureError(error instanceof Error ? error.message : 'Unable to load feature options.');
      }
    }

    void loadInitialData();
  }, []);

  useEffect(() => {
    return () => {
      if (pdfDownload) {
        URL.revokeObjectURL(pdfDownload.url);
      }
    };
  }, [pdfDownload]);

  const featureOptions = useMemo(() => featureInfo?.features ?? [], [featureInfo]);

  async function refreshMetrics() {
    setIsRefreshingMetrics(true);
    setMetricsError('');
    try {
      const response = await fetch(apiUrl('/api/metrics'));
      if (!response.ok) {
        throw new Error(await getApiError(response));
      }
      setMetrics((await response.json()) as MetricsResponse);
    } catch (error) {
      setMetricsError(error instanceof Error ? error.message : 'Unable to refresh metrics.');
    } finally {
      setIsRefreshingMetrics(false);
    }
  }

  async function handlePredict(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsPredicting(true);
    setPredictionError('');
    setPrediction(null);

    try {
      const response = await fetch(apiUrl('/api/predict'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!response.ok) {
        throw new Error(await getApiError(response));
      }
      const payload = (await response.json()) as PredictionResponse;
      setPrediction(payload);
    } catch (error) {
      setPredictionError(error instanceof Error ? error.message : 'Prediction failed.');
    } finally {
      setIsPredicting(false);
    }
  }

  async function exportPdf() {
    if (!prediction) {
      return;
    }
    setIsExportingPdf(true);
    setPredictionError('');
    setPdfMessage('');
    try {
      const response = await fetch(apiUrl('/api/export-pdf'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_data: formData, prediction_result: prediction }),
      });
      if (!response.ok) {
        throw new Error(await getApiError(response));
      }
      const filename = getDownloadFilename(response, 'student-adaptability-report.pdf');
      const url = URL.createObjectURL(await response.blob());
      setPdfDownload((current) => {
        if (current) {
          URL.revokeObjectURL(current.url);
        }
        return { url, filename };
      });
      setPdfMessage('PDF generated successfully.');
    } catch (error) {
      setPredictionError(error instanceof Error ? error.message : 'PDF export failed.');
    } finally {
      setIsExportingPdf(false);
    }
  }

  async function handleBatchUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBatchError('');
    setBatchMessage('');

    if (!selectedFile) {
      setBatchError('Please select a CSV file.');
      return;
    }

    setIsUploadingBatch(true);
    try {
      const upload = new FormData();
      upload.append('file', selectedFile);

      const response = await fetch(apiUrl('/api/predict-batch'), {
        method: 'POST',
        body: upload,
      });
      if (!response.ok) {
        throw new Error(await getApiError(response));
      }
      const filename = getDownloadFilename(response, 'batch-predictions.csv');
      downloadBlob(await response.blob(), filename);
      setBatchMessage('Batch predictions generated successfully.');
    } catch (error) {
      setBatchError(error instanceof Error ? error.message : 'Batch upload failed.');
    } finally {
      setIsUploadingBatch(false);
    }
  }

  const dashboardStats = [
    {
      label: 'Selected model',
      value: metrics?.selected_model_name ?? 'Loading',
      icon: Brain,
      tone: 'bg-teal-600',
    },
    {
      label: 'Accuracy',
      value: metrics ? `${metrics.accuracy.toFixed(2)}%` : 'Loading',
      icon: Gauge,
      tone: 'bg-indigo-600',
    },
    {
      label: 'Training records',
      value: metrics ? metrics.train_samples.toLocaleString() : 'Loading',
      icon: Database,
      tone: 'bg-amber-600',
    },
    {
      label: 'API status',
      value: health?.status === 'ok' ? 'Online' : 'Checking',
      icon: Activity,
      tone: 'bg-rose-600',
    },
  ];

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-slate-950 p-2 text-white">
                <Brain className="h-6 w-6" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-950 sm:text-2xl">
                  Student Adaptability ML Predictor
                </h1>
                <p className="mt-1 text-sm text-slate-500">
                  Flask API, scikit-learn pipeline, and React dashboard for online education readiness.
                </p>
              </div>
            </div>
          </div>

          <nav className="flex flex-wrap gap-2">
            {sections.map((section) => {
              const Icon = section.icon;
              const isActive = activeSection === section.id;
              return (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => setActiveSection(section.id)}
                  className={classNames(
                    'inline-flex min-h-10 items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition',
                    isActive
                      ? 'border-slate-950 bg-slate-950 text-white'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-teal-500 hover:text-teal-700',
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {section.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {featureError ? (
          <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" aria-hidden="true" />
              {featureError}
            </div>
          </div>
        ) : null}

        {activeSection === 'dashboard' ? (
          <section className="space-y-8">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {dashboardStats.map((stat) => (
                <StatTile key={stat.label} {...stat} />
              ))}
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-950">Project Workspace</h2>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  This full-stack app predicts a student's adaptability level from education,
                  connectivity, device, and learning environment inputs. The backend validates
                  every request, sends clean JSON errors, and keeps model preprocessing inside the
                  saved pipeline.
                </p>
                <div className="mt-5 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => setActiveSection('predict')}
                    className="inline-flex min-h-10 items-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
                  >
                    <Brain className="h-4 w-4" aria-hidden="true" />
                    Single Prediction
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveSection('batch')}
                    className="inline-flex min-h-10 items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:border-amber-500 hover:text-amber-700"
                  >
                    <Upload className="h-4 w-4" aria-hidden="true" />
                    Batch CSV
                  </button>
                </div>
              </div>

              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-950">Model Snapshot</h2>
                <div className="mt-5 space-y-4">
                  <PercentBar label="Accuracy" value={metrics?.accuracy ?? 0} />
                  <PercentBar label="Precision" value={metrics?.precision ?? 0} />
                  <PercentBar label="Recall" value={metrics?.recall ?? 0} />
                  <PercentBar label="F1-score" value={metrics?.f1_score ?? 0} />
                </div>
              </div>
            </div>
          </section>
        ) : null}

        {activeSection === 'predict' ? (
          <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <form onSubmit={handlePredict} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Single Student Prediction</h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Select the feature values and submit them to the Flask API.
                  </p>
                </div>
                <Brain className="h-6 w-6 text-teal-600" aria-hidden="true" />
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {featureOptions.map((feature) => (
                  <label key={feature.name} className="block">
                    <span className="text-sm font-medium text-slate-700">{feature.name}</span>
                    <select
                      value={formData[feature.name] ?? ''}
                      onChange={(event) =>
                        setFormData((current) => ({ ...current, [feature.name]: event.target.value }))
                      }
                      className="mt-2 h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
                    >
                      {feature.options.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>

              {predictionError ? (
                <div className="mt-5 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" aria-hidden="true" />
                    {predictionError}
                  </div>
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isPredicting || featureOptions.length === 0}
                className="mt-6 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-slate-400 sm:w-auto"
              >
                {isPredicting ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Activity className="h-4 w-4" aria-hidden="true" />
                )}
                Predict Adaptability
              </button>
            </form>

            <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Prediction Result</h2>
                  <p className="mt-1 text-sm text-slate-500">Confidence and class probabilities.</p>
                </div>
                <Gauge className="h-6 w-6 text-indigo-600" aria-hidden="true" />
              </div>

              {prediction ? (
                <div className="mt-6 space-y-6">
                  <div className="rounded-lg border border-teal-200 bg-teal-50 p-5">
                    <p className="text-sm font-medium text-teal-700">Predicted Adaptivity Level</p>
                    <p className="mt-2 text-3xl font-semibold text-teal-950">{prediction.prediction}</p>
                    <p className="mt-2 text-sm text-teal-800">
                      Confidence: {prediction.confidence.toFixed(2)}%
                    </p>
                  </div>

                  <div className="space-y-4">
                    {Object.entries(prediction.probabilities).map(([label, value]) => (
                      <PercentBar key={label} label={label} value={value} />
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={() => void exportPdf()}
                    disabled={isExportingPdf}
                    className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-indigo-500 hover:text-indigo-700 disabled:cursor-not-allowed disabled:text-slate-400"
                  >
                    {isExportingPdf ? (
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    ) : (
                      <Download className="h-4 w-4" aria-hidden="true" />
                    )}
                    Export PDF
                  </button>

                  {pdfMessage ? (
                    <div className="rounded-md border border-teal-200 bg-teal-50 p-3 text-sm text-teal-700">
                      <div className="flex flex-wrap items-center gap-2">
                        <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                        <span>{pdfMessage}</span>
                        {pdfDownload ? (
                          <>
                            <a
                              href={pdfDownload.url}
                              target="_blank"
                              rel="noreferrer"
                              className="font-semibold underline underline-offset-2"
                            >
                              View PDF
                            </a>
                            <a
                              href={pdfDownload.url}
                              download={pdfDownload.filename}
                              className="font-semibold underline underline-offset-2"
                            >
                              Download PDF
                            </a>
                          </>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="mt-6 rounded-lg border border-dashed border-slate-300 p-8 text-center">
                  <FileText className="mx-auto h-9 w-9 text-slate-400" aria-hidden="true" />
                  <p className="mt-3 text-sm text-slate-500">No prediction generated yet.</p>
                </div>
              )}
            </aside>
          </section>
        ) : null}

        {activeSection === 'batch' ? (
          <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
            <form onSubmit={handleBatchUpload} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Batch CSV Prediction</h2>
                  <p className="mt-1 text-sm text-slate-500">Upload multiple student rows and download predictions.</p>
                </div>
                <Upload className="h-6 w-6 text-amber-600" aria-hidden="true" />
              </div>

              <label className="mt-6 block">
                <span className="text-sm font-medium text-slate-700">CSV file</span>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  className="mt-2 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 file:mr-4 file:rounded-md file:border-0 file:bg-slate-950 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-slate-800"
                />
              </label>

              {batchError ? (
                <div className="mt-5 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" aria-hidden="true" />
                    {batchError}
                  </div>
                </div>
              ) : null}

              {batchMessage ? (
                <div className="mt-5 rounded-md border border-teal-200 bg-teal-50 p-3 text-sm text-teal-700">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                    {batchMessage}
                  </div>
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isUploadingBatch}
                className="mt-6 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isUploadingBatch ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Download className="h-4 w-4" aria-hidden="true" />
                )}
                Generate Predictions
              </button>
            </form>

            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">Required CSV Columns</h2>
              <div className="mt-5 grid gap-2 sm:grid-cols-2">
                {featureOptions.map((feature) => (
                  <div key={feature.name} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                    {feature.name}
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : null}

        {activeSection === 'metrics' ? (
          <section className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">Model Metrics</h2>
                <p className="mt-1 text-sm text-slate-500">Training output saved from the scikit-learn pipeline.</p>
              </div>
              <button
                type="button"
                onClick={() => void refreshMetrics()}
                disabled={isRefreshingMetrics}
                className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:border-teal-500 hover:text-teal-700 disabled:cursor-not-allowed disabled:text-slate-400"
              >
                {isRefreshingMetrics ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <RefreshCw className="h-4 w-4" aria-hidden="true" />
                )}
                Refresh
              </button>
            </div>

            {metricsError ? (
              <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" aria-hidden="true" />
                  {metricsError}
                </div>
              </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StatTile label="Accuracy" value={metrics ? `${metrics.accuracy.toFixed(2)}%` : 'Loading'} icon={Gauge} tone="bg-indigo-600" />
              <StatTile label="Precision" value={metrics ? `${metrics.precision.toFixed(2)}%` : 'Loading'} icon={Activity} tone="bg-teal-600" />
              <StatTile label="Recall" value={metrics ? `${metrics.recall.toFixed(2)}%` : 'Loading'} icon={RefreshCw} tone="bg-amber-600" />
              <StatTile label="F1-score" value={metrics ? `${metrics.f1_score.toFixed(2)}%` : 'Loading'} icon={BarChart3} tone="bg-rose-600" />
            </div>

            {metrics ? (
              <div className="grid gap-6 xl:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-950">Model Comparison</h3>
                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full min-w-[540px] border-collapse text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500">
                          <th className="py-3 pr-4 font-semibold">Model</th>
                          <th className="py-3 pr-4 font-semibold">Accuracy</th>
                          <th className="py-3 pr-4 font-semibold">Precision</th>
                          <th className="py-3 pr-4 font-semibold">Recall</th>
                          <th className="py-3 pr-4 font-semibold">F1</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(metrics.model_comparison).map(([modelName, score]) => (
                          <tr key={modelName} className="border-b border-slate-100 last:border-0">
                            <td className="py-3 pr-4 font-medium text-slate-800">
                              {modelName === metrics.selected_model_name ? `${modelName} (selected)` : modelName}
                            </td>
                            <td className="py-3 pr-4 tabular-nums">{score.accuracy.toFixed(2)}%</td>
                            <td className="py-3 pr-4 tabular-nums">{score.precision.toFixed(2)}%</td>
                            <td className="py-3 pr-4 tabular-nums">{score.recall.toFixed(2)}%</td>
                            <td className="py-3 pr-4 tabular-nums">{score.f1_score.toFixed(2)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-950">Confusion Matrix</h3>
                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full min-w-[360px] border-collapse text-center text-sm">
                      <thead>
                        <tr>
                          <th className="border border-slate-200 bg-slate-50 p-3 text-slate-500">Actual / Predicted</th>
                          {metrics.class_labels.map((label) => (
                            <th key={label} className="border border-slate-200 bg-slate-50 p-3 text-slate-700">
                              {label}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.confusion_matrix.map((row, rowIndex) => (
                          <tr key={metrics.class_labels[rowIndex]}>
                            <th className="border border-slate-200 bg-slate-50 p-3 text-slate-700">
                              {metrics.class_labels[rowIndex]}
                            </th>
                            {row.map((value, columnIndex) => (
                              <td key={`${rowIndex}-${columnIndex}`} className="border border-slate-200 p-3 tabular-nums">
                                {value}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm xl:col-span-2">
                  <h3 className="text-base font-semibold text-slate-950">Classification Report</h3>
                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full min-w-[520px] border-collapse text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500">
                          <th className="py-3 pr-4 font-semibold">Class</th>
                          <th className="py-3 pr-4 font-semibold">Precision</th>
                          <th className="py-3 pr-4 font-semibold">Recall</th>
                          <th className="py-3 pr-4 font-semibold">F1-score</th>
                          <th className="py-3 pr-4 font-semibold">Support</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.class_labels.map((label) => {
                          const entry = metrics.classification_report[label] as ClassificationReportEntry | undefined;
                          return (
                            <tr key={label} className="border-b border-slate-100 last:border-0">
                              <td className="py-3 pr-4 font-medium text-slate-800">{label}</td>
                              <td className="py-3 pr-4 tabular-nums">{entry ? (entry.precision * 100).toFixed(2) : '0.00'}%</td>
                              <td className="py-3 pr-4 tabular-nums">{entry ? (entry.recall * 100).toFixed(2) : '0.00'}%</td>
                              <td className="py-3 pr-4 tabular-nums">{entry ? (entry['f1-score'] * 100).toFixed(2) : '0.00'}%</td>
                              <td className="py-3 pr-4 tabular-nums">{entry ? entry.support : 0}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : null}
          </section>
        ) : null}

        {activeSection === 'about' ? (
          <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">About This Project</h2>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                The project predicts whether a student has Low, Moderate, or High adaptability
                for online education. It uses categorical features such as financial condition,
                network type, device, learning platform access, and institution details.
              </p>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                The ML code compares four common classifiers and saves the best complete pipeline
                with one-hot preprocessing. This keeps the implementation simple enough to explain
                while still following a professional training and inference flow.
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">Tech Stack</h2>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {['Flask API', 'React + Vite', 'TypeScript', 'Tailwind CSS', 'scikit-learn', 'ReportLab PDF'].map((item) => (
                  <div key={item} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm font-medium text-slate-700">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default App;
