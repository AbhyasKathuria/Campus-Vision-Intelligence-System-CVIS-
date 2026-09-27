import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { 
  Camera, ShieldAlert, Activity, Image as ImageIcon, 
  Settings, FileText, Radio, LogOut, ExternalLink, AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

export const OpsLayout: React.FC = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [criticalCount, setCriticalCount] = useState<number>(0);

  useEffect(() => {
    const raw = localStorage.getItem('cvis_user');
    if (raw) {
      setCurrentUser(JSON.parse(raw));
    }

    const timer = setInterval(() => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }) + ' UTC');
    }, 1000);

    // Fetch initial pending flag count
    api.listFlags({ status: 'pending' })
      .then(flags => setCriticalCount(flags.length))
      .catch(() => {});

    return () => clearInterval(timer);
  }, []);

  const handleLogout = () => {
    api.logout();
    navigate('/login');
  };

  const navClass = ({ isActive }: { isActive: boolean }) => 
    `flex items-center gap-3 px-3 py-2 rounded text-xs font-medium transition-colors ${
      isActive 
        ? 'bg-[#3DA9FC]/15 text-[#3DA9FC] border-l-2 border-[#3DA9FC]' 
        : 'text-[#8B95A7] hover:text-[#E7ECF3] hover:bg-[#131A26]'
    }`;

  return (
    <div className="flex h-screen bg-[#0B0F17] text-[#E7ECF3] font-sans overflow-hidden">
      {/* Fixed Left Sidebar */}
      <aside className="w-64 border-r border-[#232C3D] bg-[#0B0F17] flex flex-col justify-between shrink-0 select-none">
        <div>
          {/* Logo & Platform ID */}
          <div className="p-4 border-b border-[#232C3D]">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-[#3DA9FC]/20 border border-[#3DA9FC] flex items-center justify-center">
                <Radio className="w-4 h-4 text-[#3DA9FC] animate-pulse" />
              </div>
              <div>
                <h1 className="text-sm font-bold tracking-wider text-[#E7ECF3]">CVIS OPS CENTER</h1>
                <p className="text-[10px] text-[#8B95A7] tracking-tight">Vision Intelligence v1.0</p>
              </div>
            </div>
          </div>

          {/* Navigation Sections */}
          <div className="p-3 space-y-6 overflow-y-auto max-h-[calc(100vh-140px)]">
            {/* Monitoring */}
            <div>
              <p className="px-3 text-[10px] uppercase font-semibold text-[#8B95A7] tracking-wider mb-2">Monitoring</p>
              <nav className="space-y-1">
                <NavLink to="/ops" end className={navClass}>
                  <Radio className="w-4 h-4" />
                  <span>Live Camera Wall</span>
                </NavLink>
                <NavLink to="/ops/cameras" className={navClass}>
                  <Camera className="w-4 h-4" />
                  <span>Camera Registry</span>
                </NavLink>
              </nav>
            </div>

            {/* AI Analytics & Human Review */}
            <div>
              <p className="px-3 text-[10px] uppercase font-semibold text-[#8B95A7] tracking-wider mb-2">AI Analytics</p>
              <nav className="space-y-1">
                <NavLink to="/ops/reviews" className={navClass}>
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-3">
                      <ShieldAlert className="w-4 h-4" />
                      <span>Review Queue</span>
                    </div>
                    {criticalCount > 0 && (
                      <span className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-[#E5484D]/20 text-[#E5484D] border border-[#E5484D]/40">
                        {criticalCount}
                      </span>
                    )}
                  </div>
                </NavLink>
                <NavLink to="/ops/telemetry" className={navClass}>
                  <Activity className="w-4 h-4" />
                  <span>FPR Telemetry</span>
                </NavLink>
              </nav>
            </div>

            {/* Operations */}
            <div>
              <p className="px-3 text-[10px] uppercase font-semibold text-[#8B95A7] tracking-wider mb-2">Operations</p>
              <nav className="space-y-1">
                <NavLink to="/ops/events" className={navClass}>
                  <ImageIcon className="w-4 h-4" />
                  <span>Event Photo Ingest</span>
                </NavLink>
              </nav>
            </div>

            {/* System */}
            <div>
              <p className="px-3 text-[10px] uppercase font-semibold text-[#8B95A7] tracking-wider mb-2">System</p>
              <nav className="space-y-1">
                <NavLink to="/ops/audit" className={navClass}>
                  <FileText className="w-4 h-4" />
                  <span>Immutable Audit Log</span>
                </NavLink>
                <NavLink to="/ops/settings" className={navClass}>
                  <Settings className="w-4 h-4" />
                  <span>Retention & Policies</span>
                </NavLink>
              </nav>
            </div>
          </div>
        </div>

        {/* Footer & User Profile */}
        <div className="p-3 border-t border-[#232C3D] bg-[#131A26]/50">
          <div className="flex items-center justify-between mb-3 px-1">
            <div className="truncate">
              <p className="text-xs font-semibold text-[#E7ECF3] truncate">{currentUser?.name || 'Staff Reviewer'}</p>
              <p className="text-[10px] font-mono uppercase text-[#3DA9FC]">{currentUser?.role || 'reviewer'}</p>
            </div>
            <button 
              onClick={handleLogout}
              className="p-1.5 text-[#8B95A7] hover:text-[#E5484D] rounded hover:bg-[#0B0F17] transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
          <NavLink 
            to="/student"
            className="flex items-center justify-center gap-1.5 w-full py-1.5 px-2 bg-[#232C3D] hover:bg-[#232C3D]/80 text-[#E7ECF3] text-[11px] rounded transition-colors"
          >
            <span>Open Student App</span>
            <ExternalLink className="w-3 h-3 text-[#3DA9FC]" />
          </NavLink>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Status Bar */}
        <header className="h-14 border-b border-[#232C3D] bg-[#0B0F17] flex items-center justify-between px-6 shrink-0 select-none">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#131A26] border border-[#232C3D]">
              <span className="w-2 h-2 rounded-full bg-[#34C77B] animate-pulse-dot"></span>
              <span className="text-[11px] font-mono tracking-wider text-[#34C77B]">OPERATIONAL</span>
            </div>
            {criticalCount > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#E5484D]/15 border border-[#E5484D]/30 text-[#E5484D] text-xs font-mono">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>{criticalCount} PENDING REVIEW</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="font-mono text-[#8B95A7] bg-[#131A26] px-3 py-1 rounded border border-[#232C3D]">
              {currentTime || '00:00:00 UTC'}
            </div>
            <div className="text-[11px] text-[#8B95A7] flex items-center gap-1">
              <span>Policy:</span>
              <span className="font-mono text-[#E7ECF3] font-medium">Human-in-the-Loop Enforced</span>
            </div>
          </div>
        </header>

        {/* Content Canvas */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0B0F17]">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
