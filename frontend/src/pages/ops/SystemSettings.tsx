import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, Trash2, ShieldAlert, 
  Save, AlertTriangle, CheckCircle, RefreshCw 
} from 'lucide-react';
import { api } from '../../services/api';

export const OpsSystemSettings: React.FC = () => {
  const [configs, setConfigs] = useState<Record<string, any>>({
    similarity_threshold: 0.65,
    default_retention_days: 30,
    camera_cadence_seconds: 2.0,
    telemetry_min_sample_size: 10
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [purging, setPurging] = useState(false);
  const [purgeResult, setPurgeResult] = useState<any | null>(null);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await api.getSystemConfig();
      setConfigs(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await api.updateSystemConfig(configs);
      alert('System configurations updated successfully.');
    } catch (err: any) {
      alert(err.message || 'Failed to update configurations');
    } finally {
      setSaving(false);
    }
  };

  const handleManualPurge = async () => {
    if (!window.confirm("Are you sure? This will permanently delete all unconfirmed flags, raw frames, and recordings older than the retention window. Active disciplinary cases (is_retained_case = true) will be preserved.")) {
      return;
    }

    try {
      setPurging(true);
      setPurgeResult(null);
      const res = await api.purgeExpiredRecords();
      setPurgeResult(res);
    } catch (err: any) {
      alert(err.message || 'Purge failed');
    } finally {
      setPurging(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Title */}
      <div>
        <h2 className="text-base font-bold text-[#E7ECF3] flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-[#3DA9FC]" />
          <span>System Policies, Tunable Thresholds & Retention</span>
        </h2>
        <p className="text-xs text-[#8B95A7]">
          Adjust vector similarity boundaries, automated camera sampling cadence, and data retention lifecycles.
        </p>
      </div>

      {/* Configuration Form */}
      <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-5">
        <h3 className="text-xs font-bold text-[#E7ECF3] uppercase tracking-wider mb-4">
          Core Model & Operational Parameters
        </h3>

        <form onSubmit={handleSave} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Similarity Threshold */}
            <div>
              <label className="block text-xs font-semibold text-[#8B95A7] mb-1">
                Face Vector Similarity Threshold (Cosine Score)
              </label>
              <input
                type="number"
                step="0.01"
                min="0.30"
                max="0.95"
                value={configs.similarity_threshold || 0.65}
                onChange={(e) => setConfigs({ ...configs, similarity_threshold: parseFloat(e.target.value) })}
                className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
              />
              <span className="text-[10px] text-[#8B95A7] mt-1 block">
                Higher values reduce false-positive matches (recommended: 0.60 – 0.70).
              </span>
            </div>

            {/* Ingestion Cadence */}
            <div>
              <label className="block text-xs font-semibold text-[#8B95A7] mb-1">
                Default Camera Cadence (Seconds per Frame)
              </label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="10.0"
                value={configs.camera_cadence_seconds || 2.0}
                onChange={(e) => setConfigs({ ...configs, camera_cadence_seconds: parseFloat(e.target.value) })}
                className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
              />
              <span className="text-[10px] text-[#8B95A7] mt-1 block">
                Cadence of 2.0s extracts 1 frame every 2 seconds (0.5 FPS) for compliance analysis.
              </span>
            </div>

            {/* Retention Window */}
            <div>
              <label className="block text-xs font-semibold text-[#8B95A7] mb-1">
                Data Retention Window (Days)
              </label>
              <input
                type="number"
                step="1"
                min="7"
                max="180"
                value={configs.default_retention_days || 30}
                onChange={(e) => setConfigs({ ...configs, default_retention_days: parseInt(e.target.value) })}
                className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
              />
              <span className="text-[10px] text-[#8B95A7] mt-1 block">
                Auto-purge window for footage and unconfirmed flags (standard: 30 / 60 / 90 days).
              </span>
            </div>

            {/* Telemetry Sample Threshold */}
            <div>
              <label className="block text-xs font-semibold text-[#8B95A7] mb-1">
                FPR Telemetry Minimum Sample Size (N)
              </label>
              <input
                type="number"
                step="1"
                min="5"
                max="50"
                value={configs.telemetry_min_sample_size || 10}
                onChange={(e) => setConfigs({ ...configs, telemetry_min_sample_size: parseInt(e.target.value) })}
                className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
              />
              <span className="text-[10px] text-[#8B95A7] mt-1 block">
                Minimum reviewed decisions before environmental calibration alerts are declared.
              </span>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1.5 px-5 py-2 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saving ? 'Saving...' : 'Save Parameters'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Manual Data Retention Purge Action */}
      <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-5 space-y-4">
        <div>
          <h3 className="text-xs font-bold text-[#E5484D] uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" />
            <span>Automated Data Purge & Erasure Management</span>
          </h3>
          <p className="text-xs text-[#8B95A7] mt-1">
            Enforce compliance with university privacy regulations. Purges unconfirmed flags, video frames, and recordings older than the retention threshold.
          </p>
        </div>

        <div className="p-3 bg-[#0B0F17] border border-[#232C3D] rounded-lg text-xs space-y-2">
          <div className="flex items-center gap-2 text-[#34C77B]">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>Active disciplinary cases (<code className="text-[#3DA9FC]">is_retained_case = true</code>) are strictly preserved.</span>
          </div>
          <div className="flex items-center gap-2 text-[#8B95A7]">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>Immutable audit logs are never deleted.</span>
          </div>
        </div>

        {purgeResult && (
          <div className="p-3 bg-[#34C77B]/10 border border-[#34C77B]/30 rounded-lg text-xs text-[#34C77B]">
            <p className="font-bold">Purge Job Completed Successfully</p>
            <p className="text-[11px] font-mono mt-0.5">
              Purged {purgeResult.purged_flags_count} flag(s), {purgeResult.purged_recordings_count} recording(s), and {purgeResult.purged_files_count} media file(s).
            </p>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleManualPurge}
            disabled={purging}
            className="flex items-center gap-2 px-4 py-2 bg-[#E5484D]/15 hover:bg-[#E5484D]/25 border border-[#E5484D]/40 text-[#E5484D] text-xs font-bold rounded-lg transition-colors disabled:opacity-50"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{purging ? 'Executing Purge...' : 'Execute Data Purge Now'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
