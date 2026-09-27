import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, ShieldOff, AlertCircle, CheckCircle, 
  Upload, User, Lock, History, ArrowRight 
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import { Student } from '../../types';

export const StudentConsentManager: React.FC = () => {
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [enrollmentFile, setEnrollmentFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadConsent = async () => {
    try {
      setLoading(true);
      const data = await api.getConsentStatus();
      setStudent(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConsent();
  }, []);

  const handleToggleConsent = async () => {
    if (!student) return;
    try {
      setToggling(true);
      const nextState = !student.consent_status;
      const updated = await api.updateConsent(nextState);
      setStudent(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to update consent');
    } finally {
      setToggling(false);
    }
  };

  const handleEnrollmentUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enrollmentFile) return;
    try {
      setUploading(true);
      const updated = await api.uploadEnrollmentPhoto(enrollmentFile);
      setStudent(updated);
      setEnrollmentFile(null);
      alert('Official student enrollment photo uploaded and processed.');
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Biometric Consent & Privacy Dashboard
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          Manage how your university ID photo and biometric features are used across campus vision systems.
        </p>
      </div>

      {/* Main Consent Toggle Card (Armed / Disarmed Pattern) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-slate-900">
                Compliance Review Camera Recognition
              </span>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                student?.consent_status 
                  ? 'bg-emerald-100 text-emerald-800' 
                  : 'bg-slate-100 text-slate-600'
              }`}>
                {student?.consent_status ? 'CONSENT ACTIVE' : 'OPTED OUT'}
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Allow campus safety cameras to cross-reference your official student photo during routine uniform and dress-code reviews.
            </p>
          </div>

          {/* Toggle Switch */}
          <button
            onClick={handleToggleConsent}
            disabled={toggling || loading}
            className={`relative inline-flex h-8 w-14 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              student?.consent_status ? 'bg-[#0D9488]' : 'bg-slate-300'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                student?.consent_status ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Clear Guarantee Bullets */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 border-t border-slate-100 text-xs">
          <div className="p-3 bg-slate-50 rounded-xl space-y-1">
            <p className="font-semibold text-slate-800 flex items-center gap-1.5">
              <CheckCircle className="w-4 h-4 text-[#0D9488]" />
              <span>What this permits:</span>
            </p>
            <ul className="text-slate-600 space-y-1 pl-5 list-disc text-[11px]">
              <li>A reviewer can identify you if a dress-code issue is flagged.</li>
              <li>A notice can be drafted to you for informal advisory.</li>
            </ul>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl space-y-1">
            <p className="font-semibold text-slate-800 flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-[#0D9488]" />
              <span>What this strictly prevents:</span>
            </p>
            <ul className="text-slate-600 space-y-1 pl-5 list-disc text-[11px]">
              <li>No automated disciplinary action without human review.</li>
              <li>No third-party tracking or public facial search.</li>
            </ul>
          </div>
        </div>

        {/* Revocation Assurance */}
        {!student?.consent_status && (
          <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs flex items-center gap-2">
            <ShieldOff className="w-4 h-4 shrink-0" />
            <span>
              <strong>Pre-Search Isolation Active:</strong> Since you have opted out, your face embeddings have been removed from the compliance matching index. Any detections will be recorded strictly as "Unmatched (No Consent)".
            </span>
          </div>
        )}
      </div>

      {/* Student Enrollment Profile Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Official Student ID Photo on File</h3>
        
        <div className="flex items-center gap-4">
          <div className="w-20 h-24 bg-slate-100 rounded-xl overflow-hidden border border-slate-200 flex items-center justify-center shrink-0">
            {student?.enrollment_photo_ref ? (
              <img 
                src={`/media/${student.enrollment_photo_ref}`} 
                alt="Enrollment photo" 
                className="w-full h-full object-cover" 
              />
            ) : (
              <User className="w-8 h-8 text-slate-400" />
            )}
          </div>

          <div className="space-y-1 text-xs">
            <p className="font-semibold text-slate-900">
              Student ID: <span className="font-mono text-[#0D9488]">{student?.roll_number || 'STU-UNKNOWN'}</span>
            </p>
            <p className="text-slate-500">
              {student?.enrollment_photo_ref 
                ? 'Your student ID photo is linked to your campus profile.' 
                : 'No official ID photo on file yet. Upload one below.'}
            </p>
          </div>
        </div>

        {/* Upload/Update Photo */}
        <form onSubmit={handleEnrollmentUpload} className="pt-2 flex flex-col sm:flex-row gap-3">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setEnrollmentFile(e.target.files ? e.target.files[0] : null)}
            className="text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-100 hover:file:bg-slate-200"
          />
          <button
            type="submit"
            disabled={!enrollmentFile || uploading}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
          >
            {uploading ? 'Processing Face...' : 'Update ID Photo'}
          </button>
        </form>
      </div>

      {/* Link to History */}
      <div className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-2xl">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">Your Compliance History</h4>
          <p className="text-xs text-slate-500">Review any past confirmed dress-code notices issued to you.</p>
        </div>
        <Link
          to="/student/history"
          className="flex items-center gap-1.5 px-4 py-2 bg-[#0D9488]/10 hover:bg-[#0D9488]/20 text-[#0D9488] text-xs font-bold rounded-lg transition-colors"
        >
          <span>View History</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
