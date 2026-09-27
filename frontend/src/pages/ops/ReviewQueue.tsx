import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShieldAlert, CheckCircle, XCircle, AlertOctagon, Mail, 
  UserCheck, Eye, RefreshCw, AlertCircle, FileSearch, ArrowRight,
  Clock, Download, Printer, Keyboard, Undo2
} from 'lucide-react';
import { api } from '../../services/api';
import { ComplianceFlag, FlagStatus, RejectionReasonType } from '../../types';
import { NoticeComposerModal } from './NoticeComposerModal';

export const OpsReviewQueue: React.FC = () => {
  const [flags, setFlags] = useState<ComplianceFlag[]>([]);
  const [selectedFlag, setSelectedFlag] = useState<ComplianceFlag | null>(null);
  const [statusFilter, setStatusFilter] = useState<FlagStatus | 'all'>('pending');
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);

  // Rejection Modal State
  const [rejectingFlag, setRejectingFlag] = useState<ComplianceFlag | null>(null);
  const [rejectionReason, setRejectionReason] = useState<RejectionReasonType>('false_positive_clothing');
  const [rejectionNotes, setRejectionNotes] = useState('');

  // Notice Composer Modal State
  const [draftingNoticeFor, setDraftingNoticeFor] = useState<ComplianceFlag | null>(null);

  // Undo Window State (60s countdown)
  const [undoNotice, setUndoNotice] = useState<{ id: string; studentName?: string; remainingSeconds: number } | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const loadFlags = async () => {
    try {
      setLoading(true);
      const params = statusFilter === 'all' ? {} : { status: statusFilter };
      const data = await api.listFlags(params);
      setFlags(data);
      if (data.length > 0 && (!selectedFlag || !data.some(f => f.id === selectedFlag.id))) {
        setSelectedFlag(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFlags();
  }, [statusFilter]);

  // Undo Countdown Timer
  useEffect(() => {
    if (!undoNotice) return;
    if (undoNotice.remainingSeconds <= 0) {
      setUndoNotice(null);
      return;
    }
    const timer = setInterval(() => {
      setUndoNotice((prev) => {
        if (!prev || prev.remainingSeconds <= 1) return null;
        return { ...prev, remainingSeconds: prev.remainingSeconds - 1 };
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [undoNotice]);

  const handleConfirm = useCallback(async (flag: ComplianceFlag) => {
    try {
      setProcessingId(flag.id);
      await api.confirmFlag(flag.id);
      await loadFlags();
      if (selectedFlag?.id === flag.id) {
        setSelectedFlag({ ...flag, status: 'confirmed' });
      }
    } finally {
      setProcessingId(null);
    }
  }, [selectedFlag]);

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingFlag) return;
    try {
      setProcessingId(rejectingFlag.id);
      await api.rejectFlag(rejectingFlag.id, rejectionReason, rejectionNotes);
      setRejectingFlag(null);
      setRejectionNotes('');
      await loadFlags();
      if (selectedFlag?.id === rejectingFlag.id) {
        setSelectedFlag({ ...rejectingFlag, status: 'rejected', rejection_reason: rejectionReason });
      }
    } finally {
      setProcessingId(null);
    }
  };

  const handleDismiss = useCallback(async (flag: ComplianceFlag) => {
    try {
      setProcessingId(flag.id);
      await api.dismissFlag(flag.id);
      await loadFlags();
      if (selectedFlag?.id === flag.id) {
        setSelectedFlag({ ...flag, status: 'rejected' });
      }
    } finally {
      setProcessingId(null);
    }
  }, [selectedFlag]);

  const handleUndoNotice = async (noticeId: string) => {
    try {
      await api.recallNotice(noticeId);
      setUndoNotice(null);
      setToastMessage('Notice dispatch successfully recalled within 60-second safety window.');
      setTimeout(() => setToastMessage(null), 5000);
      await loadFlags();
    } catch (err: any) {
      alert(err.message || 'Failed to recall notice.');
    }
  };

  const handleExportCSV = async () => {
    try {
      const blob = await api.exportCommitteeReport('csv') as Blob;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cvis_discipline_committee_report_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Failed to export CSV report: ' + err.message);
    }
  };

  const handleExportHTML = () => {
    const token = localStorage.getItem('cvis_token');
    window.open(`/api/v1/compliance/export-report?format=html&token=${token || ''}`, '_blank');
  };

  // Keyboard Shortcuts (Phase 7.6)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in text inputs or modals open
      if (
        e.target instanceof HTMLInputElement || 
        e.target instanceof HTMLTextAreaElement || 
        draftingNoticeFor !== null || 
        rejectingFlag !== null
      ) {
        return;
      }

      if (!selectedFlag) return;

      const currentIndex = flags.findIndex(f => f.id === selectedFlag.id);

      switch (e.key) {
        case 'c':
        case 'C':
          if (selectedFlag.status === 'pending') {
            e.preventDefault();
            handleConfirm(selectedFlag);
          }
          break;
        case 'r':
        case 'R':
          if (selectedFlag.status === 'pending') {
            e.preventDefault();
            setRejectingFlag(selectedFlag);
          }
          break;
        case 'd':
        case 'D':
          if (selectedFlag.status === 'pending') {
            e.preventDefault();
            handleDismiss(selectedFlag);
          }
          break;
        case 'n':
        case 'N':
          if (selectedFlag.status === 'confirmed') {
            e.preventDefault();
            setDraftingNoticeFor(selectedFlag);
          }
          break;
        case 'ArrowDown':
        case 'j':
          if (currentIndex < flags.length - 1) {
            e.preventDefault();
            setSelectedFlag(flags[currentIndex + 1]);
          }
          break;
        case 'ArrowUp':
        case 'k':
          if (currentIndex > 0) {
            e.preventDefault();
            setSelectedFlag(flags[currentIndex - 1]);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [flags, selectedFlag, draftingNoticeFor, rejectingFlag, handleConfirm, handleDismiss]);

  const getMediaUrl = (ref?: string) => {
    if (!ref) return '/placeholder.jpg';
    return `/media/${ref}`;
  };

  return (
    <div className="space-y-4">
      {/* Header and Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#E7ECF3] flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-[#E5484D]" />
            <span>Compliance Review Queue</span>
          </h2>
          <p className="text-xs text-[#8B95A7]">
            Human-in-the-Loop decision verification: confirm or dismiss AI detections before notices are issued.
          </p>
        </div>

        {/* Action Controls: Export & Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Committee Report Exports (7.7) */}
          <div className="flex items-center gap-1.5 mr-2">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-mono bg-[#131A26] border border-[#232C3D] hover:bg-[#232C3D] text-[#E7ECF3] rounded-lg transition-colors"
              title="Download confirmed inquiries as CSV spreadsheet"
            >
              <Download className="w-3.5 h-3.5 text-[#3DA9FC]" />
              <span>CSV</span>
            </button>
            <button
              onClick={handleExportHTML}
              className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-mono bg-[#131A26] border border-[#232C3D] hover:bg-[#232C3D] text-[#E7ECF3] rounded-lg transition-colors"
              title="Print formal discipline committee dossier"
            >
              <Printer className="w-3.5 h-3.5 text-[#34C77B]" />
              <span>DOSSIER</span>
            </button>
          </div>

          {/* Status Filters */}
          <div className="flex items-center gap-1">
            {(['all', 'pending', 'confirmed', 'rejected'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase transition-colors ${
                  statusFilter === st
                    ? 'bg-[#3DA9FC] text-[#0B0F17] font-bold'
                    : 'bg-[#131A26] border border-[#232C3D] text-[#8B95A7] hover:text-[#E7ECF3]'
                }`}
              >
                {st}
              </button>
            ))}
            <button
              onClick={loadFlags}
              className="p-1.5 bg-[#131A26] border border-[#232C3D] hover:bg-[#232C3D] text-[#8B95A7] rounded-lg"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts Hint Bar (7.6) */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#0B0F17] border border-[#232C3D] rounded-lg text-[11px] text-[#8B95A7]">
        <div className="flex items-center gap-2">
          <Keyboard className="w-3.5 h-3.5 text-[#3DA9FC]" />
          <span className="font-semibold text-[#E7ECF3]">Keyboard Shortcuts:</span>
        </div>
        <div className="flex items-center gap-3 font-mono">
          <span><kbd className="px-1 py-0.5 bg-[#131A26] border border-[#232C3D] rounded text-[#E7ECF3]">C</kbd> Confirm</span>
          <span><kbd className="px-1 py-0.5 bg-[#131A26] border border-[#232C3D] rounded text-[#E7ECF3]">R</kbd> Reject</span>
          <span><kbd className="px-1 py-0.5 bg-[#131A26] border border-[#232C3D] rounded text-[#E7ECF3]">D</kbd> Dismiss</span>
          <span><kbd className="px-1 py-0.5 bg-[#131A26] border border-[#232C3D] rounded text-[#E7ECF3]">↑</kbd> <kbd className="px-1 py-0.5 bg-[#131A26] border border-[#232C3D] rounded text-[#E7ECF3]">↓</kbd> Navigate</span>
          <span><kbd className="px-1 py-0.5 bg-[#131A26] border border-[#232C3D] rounded text-[#E7ECF3]">N</kbd> Notice</span>
        </div>
      </div>

      {/* 60-Second Undo Window Banner (7.6) */}
      {undoNotice && (
        <div className="bg-[#E8A33D]/20 border border-[#E8A33D]/50 text-[#E7ECF3] px-4 py-2.5 rounded-xl flex items-center justify-between animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2 text-xs">
            <Clock className="w-4 h-4 text-[#E8A33D] animate-pulse" />
            <span>
              Notice dispatched to <strong>{undoNotice.studentName || 'Student'}</strong>. Dispatch recall window: <strong className="font-mono text-[#E8A33D]">{undoNotice.remainingSeconds}s</strong> remaining.
            </span>
          </div>
          <button
            onClick={() => handleUndoNotice(undoNotice.id)}
            className="flex items-center gap-1 px-3 py-1 bg-[#E8A33D] hover:bg-[#E8A33D]/80 text-[#0B0F17] font-bold text-xs rounded transition-colors"
          >
            <Undo2 className="w-3.5 h-3.5" />
            <span>UNDO DISPATCH</span>
          </button>
        </div>
      )}

      {/* Confirmation Toast */}
      {toastMessage && (
        <div className="bg-[#34C77B]/20 border border-[#34C77B]/40 text-[#34C77B] px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle className="w-4 h-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Split Grid: Flags Table & Detail Inspection Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Flags Table (5 cols) */}
        <div className="lg:col-span-5 bg-[#131A26] border border-[#232C3D] rounded-xl overflow-hidden flex flex-col max-h-[calc(100vh-220px)]">
          <div className="p-3 bg-[#0B0F17] border-b border-[#232C3D] flex items-center justify-between text-xs font-semibold text-[#8B95A7]">
            <span>Flags ({flags.length})</span>
            <span className="font-mono">Newest First</span>
          </div>

          <div className="overflow-y-auto divide-y divide-[#232C3D] flex-1">
            {flags.length === 0 ? (
              <div className="p-8 text-center text-[#8B95A7] text-xs">
                No flags matching current filter.
              </div>
            ) : (
              flags.map((flag) => {
                const isSelected = selectedFlag?.id === flag.id;
                return (
                  <div
                    key={flag.id}
                    onClick={() => setSelectedFlag(flag)}
                    className={`p-3 cursor-pointer transition-colors ${
                      isSelected ? 'bg-[#3DA9FC]/10 border-l-2 border-[#3DA9FC]' : 'hover:bg-[#0B0F17]/60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold uppercase ${
                        flag.status === 'pending'
                          ? 'bg-[#E5484D]/20 text-[#E5484D] border border-[#E5484D]/40'
                          : flag.status === 'confirmed'
                          ? 'bg-[#34C77B]/20 text-[#34C77B] border border-[#34C77B]/40'
                          : 'bg-[#8B95A7]/20 text-[#8B95A7]'
                      }`}>
                        {flag.status}
                      </span>
                      <span className="text-[10px] font-mono text-[#8B95A7]">
                        {new Date(flag.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <p className="text-xs font-bold text-[#E7ECF3] truncate">
                      {flag.violation_type.replace('_', ' ').toUpperCase()}
                    </p>

                    <div className="flex items-center justify-between mt-1 text-[11px]">
                      <span className="text-[#8B95A7] truncate max-w-[150px]">
                        {flag.camera_name || 'Camera Feed'}
                      </span>
                      {flag.matched_student_name ? (
                        <span className="text-[#3DA9FC] font-mono font-medium">
                          {flag.matched_student_roll}
                        </span>
                      ) : (
                        <span className="text-[#E8A33D] font-mono text-[10px]">
                          {flag.unmatched_reason === 'no_consent' ? 'UNMATCHED (NO CONSENT)' : 'UNMATCHED'}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Detailed Side-by-Side Review Inspector (7 cols) */}
        <div className="lg:col-span-7 bg-[#131A26] border border-[#232C3D] rounded-xl p-5 space-y-5 overflow-y-auto max-h-[calc(100vh-220px)]">
          {selectedFlag ? (
            <>
              {/* Top Banner: Status & Confidence Summary */}
              <div className="flex items-center justify-between border-b border-[#232C3D] pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-[#E7ECF3] uppercase tracking-wide">
                      {selectedFlag.violation_type.replace('_', ' ')}
                    </h3>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#E8A33D]/20 text-[#E8A33D] border border-[#E8A33D]/40">
                      AI Confidence: {Math.round(selectedFlag.violation_confidence * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-[#8B95A7] mt-0.5">
                    Location: {selectedFlag.camera_name} • Zone: {selectedFlag.camera_zone}
                  </p>
                </div>

                {selectedFlag.is_retained_case && (
                  <span className="px-2 py-1 bg-[#3DA9FC]/20 text-[#3DA9FC] border border-[#3DA9FC]/40 text-[10px] font-mono font-bold rounded">
                    RETAINED DISCIPLINARY CASE
                  </span>
                )}
              </div>

              {/* Side-by-Side Visual Comparison */}
              <div>
                <p className="text-xs font-semibold text-[#8B95A7] uppercase tracking-wider mb-2">
                  Biometric Verification Side-by-Side
                </p>
                <div className="grid grid-cols-2 gap-4">
                  {/* Left: Captured Face Crop from Feed */}
                  <div className="bg-[#0B0F17] border border-[#232C3D] rounded-lg p-3 text-center">
                    <p className="text-[11px] font-mono text-[#8B95A7] mb-2">CCTV CAPTURE CROP</p>
                    <div className="aspect-square bg-black/50 rounded-lg overflow-hidden flex items-center justify-center border border-[#232C3D]">
                      <img 
                        src={getMediaUrl(selectedFlag.face_crop_ref || selectedFlag.frame_ref)} 
                        alt="Captured face" 
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <p className="text-[10px] font-mono text-[#8B95A7] mt-2">
                      Timestamp: {selectedFlag.frame_timestamp_ms}ms
                    </p>
                  </div>

                  {/* Right: Enrolled Student Photo */}
                  <div className="bg-[#0B0F17] border border-[#232C3D] rounded-lg p-3 text-center">
                    <p className="text-[11px] font-mono text-[#8B95A7] mb-2">ENROLLED STUDENT PROFILE</p>
                    <div className="aspect-square bg-black/50 rounded-lg overflow-hidden flex items-center justify-center border border-[#232C3D]">
                      {selectedFlag.matched_student_id ? (
                        <img 
                          src={getMediaUrl(selectedFlag.enrollment_photo_ref)} 
                          alt="Enrolled student" 
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="flex flex-col items-center justify-center p-4 text-[#8B95A7] text-xs">
                          <AlertCircle className="w-8 h-8 text-[#E8A33D] mb-1" />
                          <span>No Enrolled Match</span>
                          <span className="text-[10px] text-[#E8A33D] font-mono mt-1">
                            {selectedFlag.unmatched_reason === 'no_consent' ? 'BIOMETRIC CONSENT WITHHELD' : 'LOW SIMILARITY SCORE'}
                          </span>
                        </div>
                      )}
                    </div>
                    {selectedFlag.matched_student_name ? (
                      <div className="mt-2 text-xs">
                        <p className="font-semibold text-[#E7ECF3]">{selectedFlag.matched_student_name}</p>
                        <p className="text-[10px] font-mono text-[#3DA9FC]">
                          {selectedFlag.matched_student_roll} • {Math.round((selectedFlag.match_confidence || 0) * 100)}% match
                        </p>
                      </div>
                    ) : (
                      <p className="text-[10px] font-mono text-[#8B95A7] mt-2">PII Protected</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Heuristic / Feature Explanation Pills */}
              <div>
                <p className="text-xs font-semibold text-[#8B95A7] uppercase tracking-wider mb-2">
                  AI Explainability Metrics & Features
                </p>
                <div className="p-3 bg-[#0B0F17] border border-[#232C3D] rounded-lg">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono">
                    {selectedFlag.violation_details && Object.entries(selectedFlag.violation_details).map(([k, v]) => (
                      <div key={k} className="p-2 bg-[#131A26] rounded border border-[#232C3D]">
                        <span className="text-[#8B95A7] text-[10px] block truncate">{k}</span>
                        <span className="text-[#E7ECF3] font-bold">
                          {typeof v === 'boolean' ? (v ? 'TRUE' : 'FALSE') : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Rejection Details if rejected */}
              {selectedFlag.status === 'rejected' && (
                <div className="p-3 bg-[#E5484D]/10 border border-[#E5484D]/30 rounded-lg text-xs space-y-1">
                  <p className="text-[#E5484D] font-bold uppercase font-mono">Rejected by Reviewer</p>
                  <p className="text-[#8B95A7]">Reason: <span className="text-[#E7ECF3] font-mono">{selectedFlag.rejection_reason}</span></p>
                  {selectedFlag.rejection_notes && (
                    <p className="text-[#8B95A7]">Notes: {selectedFlag.rejection_notes}</p>
                  )}
                </div>
              )}

              {/* Reviewer Action Buttons */}
              <div className="border-t border-[#232C3D] pt-4 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleConfirm(selectedFlag)}
                    disabled={processingId === selectedFlag.id || selectedFlag.status === 'confirmed'}
                    className="flex items-center gap-1.5 px-4 py-2 bg-[#34C77B] hover:bg-[#34C77B]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors shadow-lg shadow-[#34C77B]/10 disabled:opacity-50"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Confirm Match & Violation</span>
                  </button>

                  <button
                    onClick={() => setRejectingFlag(selectedFlag)}
                    disabled={processingId === selectedFlag.id || selectedFlag.status === 'rejected'}
                    className="flex items-center gap-1.5 px-4 py-2 bg-[#E5484D]/15 hover:bg-[#E5484D]/25 border border-[#E5484D]/30 text-[#E5484D] text-xs font-bold rounded-lg transition-colors disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject Flag</span>
                  </button>

                  <button
                    onClick={() => handleDismiss(selectedFlag)}
                    disabled={processingId === selectedFlag.id}
                    className="px-3 py-2 bg-[#232C3D] hover:bg-[#232C3D]/80 text-[#8B95A7] hover:text-[#E7ECF3] text-xs font-medium rounded-lg transition-colors"
                  >
                    Dismiss
                  </button>
                </div>

                {selectedFlag.status === 'confirmed' && selectedFlag.matched_student_id && (
                  <button
                    onClick={() => setDraftingNoticeFor(selectedFlag)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors shadow-lg shadow-[#3DA9FC]/20"
                  >
                    <Mail className="w-4 h-4" />
                    <span>Draft Notice</span>
                  </button>
                )}
              </div>
            </>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-[#8B95A7] text-xs">
              <FileSearch className="w-10 h-10 mb-2 opacity-50" />
              <span>Select a flag from the queue to inspect details</span>
            </div>
          )}
        </div>
      </div>

      {/* Typed Rejection Modal */}
      {rejectingFlag && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-[#131A26] border border-[#232C3D] w-full max-w-md rounded-xl p-5 shadow-2xl">
            <h3 className="text-sm font-bold text-[#E7ECF3] mb-1">Specify Rejection Reason</h3>
            <p className="text-xs text-[#8B95A7] mb-4">
              Your feedback standardizes FPR telemetry and helps calibrate environmental camera sensors.
            </p>

            <form onSubmit={handleRejectSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Standardized Category</label>
                <select
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value as RejectionReasonType)}
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
                >
                  <option value="false_positive_clothing">Patterned Shirt / False Waistline Edge</option>
                  <option value="lighting_contrast_artifact">Lighting / Contrast / Shadow Artifact</option>
                  <option value="student_posture_angle">Student Posture / Bending / Oblique Angle</option>
                  <option value="incorrect_identity_match">Incorrect Identity Match (Wrong Person)</option>
                  <option value="no_violation_found">No Violation Found (Clothing Compliant)</option>
                  <option value="other">Other Environmental Factor</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Reviewer Notes (Optional)</label>
                <textarea
                  rows={3}
                  value={rejectionNotes}
                  onChange={(e) => setRejectionNotes(e.target.value)}
                  placeholder="e.g. Morning sun flare washed out collar edges."
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRejectingFlag(null)}
                  className="px-3 py-1.5 bg-[#232C3D] hover:bg-[#232C3D]/80 text-[#E7ECF3] text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={processingId !== null}
                  className="px-4 py-1.5 bg-[#E5484D] hover:bg-[#E5484D]/80 text-white text-xs font-bold rounded-lg transition-colors"
                >
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Notice Composer Modal */}
      {draftingNoticeFor && (
        <NoticeComposerModal
          flag={draftingNoticeFor}
          onClose={() => setDraftingNoticeFor(null)}
          onSuccess={(sentNotice) => {
            const studentName = draftingNoticeFor.matched_student_name || 'Student';
            setDraftingNoticeFor(null);
            loadFlags();
            setUndoNotice({
              id: sentNotice.id,
              studentName: studentName,
              remainingSeconds: 60
            });
          }}
        />
      )}
    </div>
  );
};
