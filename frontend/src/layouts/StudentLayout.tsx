import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Camera, ShieldCheck, History, LogOut, LayoutDashboard } from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

export const StudentLayout: React.FC = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem('cvis_user');
    if (raw) {
      setCurrentUser(JSON.parse(raw));
    }
  }, []);

  const handleLogout = () => {
    api.logout();
    navigate('/login');
  };

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
      isActive 
        ? 'bg-[#0D9488]/10 text-[#0D9488] font-semibold' 
        : 'text-[#64748B] hover:text-[#0F172A] hover:bg-slate-100'
    }`;

  return (
    <div className="min-h-screen bg-[#FAFAF8] text-[#0F172A] flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#0D9488] flex items-center justify-center text-white shadow-sm shadow-[#0D9488]/20">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-[#0F172A]">Campus Vision</span>
              <span className="text-xs text-[#0D9488] font-medium ml-1.5 bg-[#0D9488]/10 px-2 py-0.5 rounded-full">Student Portal</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-2">
            <NavLink to="/student" end className={navClass}>
              <Camera className="w-4 h-4" />
              <span>Find Photos</span>
            </NavLink>
            <NavLink to="/student/consent" className={navClass}>
              <ShieldCheck className="w-4 h-4" />
              <span>Consent & Privacy</span>
            </NavLink>
            <NavLink to="/student/history" className={navClass}>
              <History className="w-4 h-4" />
              <span>My History</span>
            </NavLink>
          </nav>

          {/* User Profile & Actions */}
          <div className="flex items-center gap-3">
            <NavLink 
              to="/ops"
              className="text-xs text-[#64748B] hover:text-[#0D9488] flex items-center gap-1 bg-slate-100 hover:bg-slate-200 px-2.5 py-1.5 rounded-lg transition-colors"
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Ops Console</span>
            </NavLink>
            <div className="h-4 w-[1px] bg-slate-200"></div>
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-[#0F172A]">{currentUser?.name || 'Student'}</p>
              <p className="text-[11px] text-[#64748B]">{currentUser?.email || 'student@campus.edu'}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
          <p>© 2026 University Vision Intelligence System. Opt-in Biometric Privacy Architecture.</p>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-[#0D9488]">
              <span className="w-2 h-2 rounded-full bg-[#0D9488]"></span>
              Ephemeral Search Active
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};
