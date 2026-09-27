import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Radio, Lock, Mail, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await api.login(email, password);
      if (res.user.role === 'student') {
        navigate('/student');
      } else {
        navigate('/ops');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('Password123!');
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col justify-center items-center p-4 font-sans text-[#E7ECF3]">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-[#3DA9FC]/15 border border-[#3DA9FC] flex items-center justify-center mx-auto text-[#3DA9FC] shadow-lg shadow-[#3DA9FC]/20">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#E7ECF3]">
            Campus Vision Intelligence System
          </h1>
          <p className="text-xs text-[#8B95A7]">
            Event Photo Discovery & Human-in-the-Loop Compliance Review
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-2xl p-6 shadow-2xl space-y-5">
          {error && (
            <div className="p-3 bg-[#E5484D]/15 border border-[#E5484D]/30 text-[#E5484D] text-xs rounded-xl flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Campus Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#8B95A7] absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@campus.edu"
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-xl pl-9 pr-3 py-2.5 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#8B95A7] absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-xl pl-9 pr-3 py-2.5 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-xl transition-colors shadow-lg shadow-[#3DA9FC]/20 disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to Campus Vision'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Credentials Shortcut */}
          <div className="pt-4 border-t border-[#232C3D] space-y-2">
            <p className="text-[10px] font-mono text-[#8B95A7] uppercase tracking-wider text-center">
              Quick Switch Demo Roles
            </p>
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <button
                type="button"
                onClick={() => handleQuickDemo('reviewer@campus.edu')}
                className="p-2 bg-[#0B0F17] hover:bg-[#232C3D] border border-[#232C3D] rounded-lg text-left"
              >
                <span className="text-[#3DA9FC] block font-bold">Reviewer</span>
                <span className="text-[#8B95A7] text-[10px]">Warden Pendelton</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemo('admin@campus.edu')}
                className="p-2 bg-[#0B0F17] hover:bg-[#232C3D] border border-[#232C3D] rounded-lg text-left"
              >
                <span className="text-[#34C77B] block font-bold">Administrator</span>
                <span className="text-[#8B95A7] text-[10px]">System Admin</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemo('alice@campus.edu')}
                className="p-2 bg-[#0B0F17] hover:bg-[#232C3D] border border-[#232C3D] rounded-lg text-left"
              >
                <span className="text-[#0D9488] block font-bold">Student (Consented)</span>
                <span className="text-[#8B95A7] text-[10px]">Alice Walker</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemo('carol@campus.edu')}
                className="p-2 bg-[#0B0F17] hover:bg-[#232C3D] border border-[#232C3D] rounded-lg text-left"
              >
                <span className="text-[#E8A33D] block font-bold">Student (No Consent)</span>
                <span className="text-[#8B95A7] text-[10px]">Carol Danvers</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer Policy Badge */}
        <div className="text-center text-[11px] text-[#8B95A7] flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-[#34C77B]" />
          <span>Biometric Protection & Human Oversight Guarantee Enforced</span>
        </div>
      </div>
    </div>
  );
};
