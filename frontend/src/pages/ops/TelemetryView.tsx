import React, { useState, useEffect } from 'react';
import { 
  Activity, AlertTriangle, ShieldCheck, Camera, 
  BarChart3, RefreshCw, Info, CheckCircle2 
} from 'lucide-react';
import { api } from '../../services/api';
import { TelemetryResponse } from '../../types';

export const OpsTelemetryView: React.FC = () => {
  const [telemetry, setTelemetry] = useState<TelemetryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadTelemetry = async () => {
    try {
      setLoading(true);
      const data = await api.getTelemetry();
      setTelemetry(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTelemetry();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-[#E7ECF3] flex items-center gap-2">
            <Activity className="w-5 h-5 text-[#3DA9FC]" />
            <span>Model Efficacy & False-Positive Rate (FPR) Telemetry</span>
          </h2>
          <p className="text-xs text-[#8B95A7]">
            Continuous feedback loop from human reviewer decisions, segmented by heuristic type and camera zone.
          </p>
        </div>
        <button
          onClick={loadTelemetry}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-[#131A26] border border-[#232C3D] hover:bg-[#232C3D] rounded-lg transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Overall FPR */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-4">
          <p className="text-[11px] font-medium text-[#8B95A7] uppercase tracking-wider">Overall Reviewer Rejection Rate</p>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-bold font-mono text-[#E8A33D]">
              {telemetry?.overall_fpr_percentage !== null && telemetry?.overall_fpr_percentage !== undefined
                ? `${telemetry.overall_fpr_percentage}%`
                : 'N/A'}
            </span>
            <span className="text-xs text-[#8B95A7]">
              {telemetry?.status_label === 'insufficient_data' ? 'Insufficient Data' : 'FPR Across Heuristics'}
            </span>
          </div>
          <p className="text-[10px] text-[#8B95A7] mt-2">
            {telemetry && telemetry.total_flags_reviewed < telemetry.min_sample_size
              ? `N=${telemetry.total_flags_reviewed} (Requires N ≥ ${telemetry.min_sample_size} for statistical significance)`
              : `Based on ${telemetry?.total_flags_reviewed || 0} total reviewed decisions`}
          </p>
        </div>

        {/* Statistical Guard */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-4">
          <p className="text-[11px] font-medium text-[#8B95A7] uppercase tracking-wider">Statistical Significance Guard</p>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-bold font-mono text-[#3DA9FC]">
              N ≥ {telemetry?.min_sample_size || 15}
            </span>
            <span className="text-xs text-[#8B95A7]">Sample Threshold</span>
          </div>
          <p className="text-[10px] text-[#8B95A7] mt-2">
            Low sample pairs (&lt;{telemetry?.min_sample_size || 15}) are shielded from triggering false calibration alerts.
          </p>
        </div>

        {/* System Calibration Status */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-4">
          <p className="text-[11px] font-medium text-[#8B95A7] uppercase tracking-wider">Active Calibration Alerts</p>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-bold font-mono text-[#E5484D]">
              {telemetry?.by_camera.filter(c => c.environmental_calibration_recommended).length || 0}
            </span>
            <span className="text-xs text-[#8B95A7]">Sensors Highlighted</span>
          </div>
          <p className="text-[10px] text-[#8B95A7] mt-2">
            Requires camera repositioning or lighting adjustment
          </p>
        </div>
      </div>

      {/* Per-Violation Type Breakdown */}
      <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-5">
        <h3 className="text-xs font-bold text-[#E7ECF3] uppercase tracking-wider mb-3">
          False-Positive Rate by Violation Heuristic
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {telemetry?.by_violation.map((item) => (
            <div key={item.violation_type} className="p-3 bg-[#0B0F17] border border-[#232C3D] rounded-lg">
              <p className="text-xs font-bold text-[#E7ECF3] uppercase truncate mb-1">
                {item.violation_type.replace(/_/g, ' ')}
              </p>
              <div className="flex items-baseline justify-between mb-2">
                {item.status_label === 'insufficient_data' || item.fpr_percentage === null || item.fpr_percentage === undefined ? (
                  <span className="text-[11px] font-mono text-[#8B95A7] bg-[#232C3D]/60 px-1.5 py-0.5 rounded">
                    Insufficient Data (N &lt; {telemetry?.min_sample_size || 15})
                  </span>
                ) : (
                  <span className="text-xl font-bold font-mono text-[#E8A33D]">{item.fpr_percentage}%</span>
                )}
                <span className="text-[10px] text-[#8B95A7] font-mono">{item.rejected_count} / {item.total_reviewed} rejected</span>
              </div>
              <div className="w-full bg-[#232C3D] h-1.5 rounded-full overflow-hidden">
                <div 
                  className="bg-[#E8A33D] h-full rounded-full transition-all"
                  style={{ width: `${item.fpr_percentage != null ? Math.min(100, item.fpr_percentage) : 0}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Camera- & Zone-Segmented Telemetry (User Highlighted Requirement) */}
      <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-xs font-bold text-[#E7ECF3] uppercase tracking-wider">
              Camera & Zone Segmentation
            </h3>
            <p className="text-[11px] text-[#8B95A7]">
              Isolates hardware, lighting, and environmental factors from global heuristic models.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0F17] text-[#8B95A7] font-mono uppercase text-[10px] border-b border-[#232C3D]">
              <tr>
                <th className="p-3">Camera Sensor</th>
                <th className="p-3">Zone</th>
                <th className="p-3 text-right">Reviewed (N)</th>
                <th className="p-3 text-right">FPR %</th>
                <th className="p-3">Leading Rejection Factor</th>
                <th className="p-3">Status Tag</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232C3D] font-mono">
              {telemetry?.by_camera.map((cam) => (
                <tr key={cam.camera_id} className="hover:bg-[#0B0F17]/50 transition-colors">
                  <td className="p-3 font-sans font-semibold text-[#E7ECF3]">
                    <div className="flex items-center gap-2">
                      <Camera className="w-3.5 h-3.5 text-[#3DA9FC]" />
                      <span>{cam.camera_name}</span>
                    </div>
                  </td>
                  <td className="p-3 text-[#8B95A7]">{cam.zone}</td>
                  <td className="p-3 text-right text-[#E7ECF3]">{cam.total_reviewed}</td>
                  <td className="p-3 text-right font-bold text-[#E8A33D]">
                    {cam.status_label === 'insufficient_data' || cam.fpr_percentage === null || cam.fpr_percentage === undefined
                      ? '—'
                      : `${cam.fpr_percentage}%`}
                  </td>
                  <td className="p-3 text-[#8B95A7] text-[11px]">
                    {cam.leading_rejection_reason ? cam.leading_rejection_reason.replace(/_/g, ' ') : 'None'}
                  </td>
                  <td className="p-3">
                    {cam.status_label === 'insufficient_data' ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#8B95A7]/10 text-[#8B95A7] border border-[#8B95A7]/30 text-[10px]">
                        <Info className="w-3 h-3" />
                        <span>INSUFFICIENT DATA (N &lt; {telemetry?.min_sample_size || 15})</span>
                      </span>
                    ) : cam.environmental_calibration_recommended ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#E5484D]/20 text-[#E5484D] border border-[#E5484D]/40 text-[10px] font-bold">
                        <AlertTriangle className="w-3 h-3" />
                        <span>ENVIRONMENTAL CALIBRATION RECOMMENDED</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#34C77B]/10 text-[#34C77B] text-[10px]">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>CALIBRATED / WITHIN TOLERANCE</span>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rejection Reason Distribution */}
      <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-5">
        <h3 className="text-xs font-bold text-[#E7ECF3] uppercase tracking-wider mb-3">
          Typed Rejection Reason Distribution
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {telemetry && Object.entries(telemetry.rejection_reason_distribution).map(([reason, count]) => (
            <div key={reason} className="p-3 bg-[#0B0F17] border border-[#232C3D] rounded-lg">
              <span className="text-[10px] font-mono text-[#8B95A7] block truncate">
                {reason.replace('_', ' ').toUpperCase()}
              </span>
              <span className="text-xl font-bold font-mono text-[#E7ECF3] mt-1 block">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
