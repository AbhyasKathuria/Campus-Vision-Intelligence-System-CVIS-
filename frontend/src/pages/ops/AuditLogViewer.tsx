import React, { useState, useEffect } from 'react';
import { FileText, RefreshCw, Filter, ShieldCheck, User } from 'lucide-react';
import { api } from '../../services/api';
import { AuditLog } from '../../types';

export const OpsAuditLogViewer: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await api.listAuditLogs();
      setLogs(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-[#E7ECF3] flex items-center gap-2">
            <FileText className="w-5 h-5 text-[#3DA9FC]" />
            <span>Immutable Privacy & Decision Audit Trail</span>
          </h2>
          <p className="text-xs text-[#8B95A7]">
            Verifiable log of every biometric search, review confirmation, notice dispatch, consent change, and data purge.
          </p>
        </div>

        <button
          onClick={loadLogs}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-[#131A26] border border-[#232C3D] hover:bg-[#232C3D] rounded-lg transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Logs Table */}
      <div className="bg-[#131A26] border border-[#232C3D] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0B0F17] text-[#8B95A7] uppercase text-[10px] border-b border-[#232C3D]">
              <tr>
                <th className="p-3">Timestamp (UTC)</th>
                <th className="p-3">Action</th>
                <th className="p-3">Actor Role</th>
                <th className="p-3">Target Entity</th>
                <th className="p-3">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232C3D]">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-[#0B0F17]/50 transition-colors">
                  <td className="p-3 text-[#8B95A7] whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="p-3">
                    <span className="font-bold text-[#3DA9FC]">{log.action}</span>
                  </td>
                  <td className="p-3 text-[#E7ECF3]">
                    <span className="px-1.5 py-0.5 rounded bg-[#232C3D] text-[10px]">
                      {log.actor_role || 'SYSTEM'}
                    </span>
                  </td>
                  <td className="p-3 text-[#8B95A7]">
                    {log.target_type} : <span className="text-[#E7ECF3]">{log.target_id.slice(0, 8)}</span>
                  </td>
                  <td className="p-3 text-[#8B95A7] text-[10px] max-w-xs truncate">
                    {log.metadata_json ? JSON.stringify(log.metadata_json) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
