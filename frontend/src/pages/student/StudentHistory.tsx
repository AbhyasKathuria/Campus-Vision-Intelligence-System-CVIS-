import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, Calendar, MapPin, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { ComplianceFlag } from '../../types';

export const StudentHistoryView: React.FC = () => {
  const [history, setHistory] = useState<ComplianceFlag[]>([]);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getStudentHistory();
      setHistory(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Your Compliance History
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Confirmed advisories and dress-code notices issued after human review.
          </p>
        </div>

        <button
          onClick={loadHistory}
          className="p-2 border border-slate-200 hover:bg-slate-100 rounded-lg text-slate-500"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* History Items */}
      {history.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-50 text-[#0D9488] flex items-center justify-center mx-auto">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Clean Record</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            You have no confirmed compliance advisories or dress-code flags on your student record.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((flag) => (
            <div key={flag.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full uppercase">
                  {flag.violation_type.replace('_', ' ')}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(flag.created_at).toLocaleDateString()}
                </span>
              </div>

              <div className="text-xs text-slate-600 space-y-1">
                <p className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>Observed Location: {flag.camera_name || 'Campus Building'} ({flag.camera_zone || 'Academic'})</span>
                </p>
                {flag.reviewer_notes && (
                  <p className="p-3 bg-slate-50 rounded-xl text-slate-700 border border-slate-100 mt-2">
                    <strong>Reviewer Notes:</strong> {flag.reviewer_notes}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
