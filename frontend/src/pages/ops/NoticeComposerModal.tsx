import React, { useState } from 'react';
import { Mail, Send, X, AlertCircle, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { ComplianceFlag, Notice } from '../../types';

interface NoticeComposerProps {
  flag: ComplianceFlag;
  onClose: () => void;
  onSuccess: (notice: Notice) => void;
}

export const NoticeComposerModal: React.FC<NoticeComposerProps> = ({ flag, onClose, onSuccess }) => {
  const [subject, setSubject] = useState(
    `Campus Uniform Advisory: ${flag.violation_type.replace('_', ' ').toUpperCase()}`
  );
  const [content, setContent] = useState(
    `Dear ${flag.matched_student_name || 'Student'},\n\n` +
    `During routine operations on ${new Date(flag.created_at).toLocaleDateString()}, you were observed at ${flag.camera_name || 'campus'} with a potential uniform non-compliance (${flag.violation_type.replace('_', ' ')}).\n\n` +
    `Please review the student code of conduct to ensure appropriate attire is maintained.\n\n` +
    `Regards,\nDiscipline Committee`
  );
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSending(true);
      setError(null);
      // Step 1: Draft Notice
      const draft = await api.draftNotice(flag.id, subject, content);
      // Step 2: Send Notice (Reviewer approval)
      const sent = await api.sendNotice(draft.id);
      onSuccess(sent);
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch notice.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-[#131A26] border border-[#232C3D] w-full max-w-xl rounded-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="p-4 border-b border-[#232C3D] flex items-center justify-between bg-[#0B0F17]">
          <div className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-[#3DA9FC]" />
            <h3 className="text-sm font-bold text-[#E7ECF3]">Draft & Dispatch Compliance Notice</h3>
          </div>
          <button 
            onClick={onClose}
            className="text-[#8B95A7] hover:text-[#E7ECF3] p-1 rounded hover:bg-[#232C3D]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-[#E5484D]/15 border border-[#E5484D]/30 text-[#E5484D] text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Student & Violation Summary */}
          <div className="p-3 bg-[#0B0F17] border border-[#232C3D] rounded-lg text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-[#8B95A7]">Recipient Student:</span>
              <span className="text-[#E7ECF3] font-semibold">{flag.matched_student_name} ({flag.matched_student_roll})</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8B95A7]">Observed Location:</span>
              <span className="text-[#E7ECF3]">{flag.camera_name} ({flag.camera_zone})</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8B95A7]">Violation Category:</span>
              <span className="text-[#E8A33D] font-mono uppercase">{flag.violation_type.replace('_', ' ')}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Notice Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Message Content</label>
            <textarea
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
            />
          </div>

          {/* Retention & Human In The Loop Notice */}
          <div className="p-3 bg-[#3DA9FC]/10 border border-[#3DA9FC]/30 rounded-lg flex items-start gap-2.5 text-[11px] text-[#3DA9FC]">
            <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Human-in-the-Loop Confirmation & Case Retention</p>
              <p className="text-[#8B95A7] mt-0.5">
                Dispatching this notice explicitly marks the underlying flag as an active disciplinary case (<code className="text-[#3DA9FC]">is_retained_case = true</code>), preserving it from the scheduled data retention purge.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-[#232C3D] hover:bg-[#232C3D]/80 text-[#E7ECF3] text-xs font-medium rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={sending}
              className="flex items-center gap-2 px-5 py-2 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors shadow-lg shadow-[#3DA9FC]/20"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{sending ? 'Dispatching...' : 'Approve & Dispatch Notice'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
