import React, { useState, useEffect } from 'react';
import { 
  Camera as CameraIcon, ShieldAlert, Activity, Users, 
  Radio, Play, AlertTriangle, CheckCircle2, RefreshCw 
} from 'lucide-react';
import { api } from '../../services/api';
import { Camera, ComplianceFlag } from '../../types';

export const OpsDashboard: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [pendingFlags, setPendingFlags] = useState<ComplianceFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [cams, flags] = await Promise.all([
        api.listCameras(),
        api.listFlags({ status: 'pending' })
      ]);
      setCameras(cams);
      setPendingFlags(flags);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulateFeed = async (cameraId: string) => {
    try {
      setSimulating(cameraId);
      // Create a dummy recording to trigger simulated frame processing
      const dummyFile = new File(["dummy video stream data"], "simulated_stream.mp4", { type: "video/mp4" });
      const rec = await api.createCamera({ id: cameraId }); // ensure camera exists
      // Call compliance process endpoint
      await fetch(`/api/v1/compliance/process-recording/simulated_${cameraId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('cvis_token')}`
        }
      }).catch(() => {});
      await loadData();
    } finally {
      setSimulating(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Glanceable Metrics Top Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Cameras Online */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-[#8B95A7] uppercase tracking-wider">Cameras Online</p>
            <p className="text-2xl font-bold font-mono text-[#E7ECF3] mt-1">
              {cameras.filter(c => c.active).length} <span className="text-xs text-[#8B95A7] font-normal">/ {cameras.length} active</span>
            </p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-[#34C77B]/10 border border-[#34C77B]/30 flex items-center justify-center">
            <Radio className="w-5 h-5 text-[#34C77B]" />
          </div>
        </div>

        {/* Metric 2: Review Queue Pending */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-[#8B95A7] uppercase tracking-wider">Review Queue Pending</p>
            <p className="text-2xl font-bold font-mono text-[#E5484D] mt-1">
              {pendingFlags.length} <span className="text-xs text-[#8B95A7] font-normal">awaiting staff</span>
            </p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-[#E5484D]/10 border border-[#E5484D]/30 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-[#E5484D]" />
          </div>
        </div>

        {/* Metric 3: Today's Flags Processed */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-[#8B95A7] uppercase tracking-wider">Detection Cadence</p>
            <p className="text-2xl font-bold font-mono text-[#3DA9FC] mt-1">
              0.5 <span className="text-xs text-[#8B95A7] font-normal">FPS (2.0s sample)</span>
            </p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-[#3DA9FC]/10 border border-[#3DA9FC]/30 flex items-center justify-center">
            <Activity className="w-5 h-5 text-[#3DA9FC]" />
          </div>
        </div>

        {/* Metric 4: Human-in-the-Loop Guard */}
        <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-[#8B95A7] uppercase tracking-wider">Autonomous Notices</p>
            <p className="text-2xl font-bold font-mono text-[#34C77B] mt-1">
              0 <span className="text-xs text-[#8B95A7] font-normal">(Blocked by policy)</span>
            </p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-[#34C77B]/10 border border-[#34C77B]/30 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-[#34C77B]" />
          </div>
        </div>
      </div>

      {/* Main Content Block: Live Camera Wall */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-[#E7ECF3] flex items-center gap-2">
              <span>Live CCTV Ingestion Feeds</span>
              <span className="w-2 h-2 rounded-full bg-[#34C77B] animate-pulse-dot"></span>
            </h2>
            <p className="text-xs text-[#8B95A7]">Continuous cadence frame sampling with real-time detection bounding overlays</p>
          </div>
          <button 
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-[#131A26] border border-[#232C3D] hover:bg-[#232C3D] rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>REFRESH</span>
          </button>
        </div>

        {/* Camera Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
          {cameras.map((camera, idx) => (
            <div 
              key={camera.id}
              className="bg-[#131A26] border border-[#232C3D] rounded-xl overflow-hidden flex flex-col group hover:border-[#3DA9FC]/50 transition-colors"
            >
              {/* Camera Header */}
              <div className="p-3 bg-[#0B0F17]/70 border-b border-[#232C3D] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#34C77B] animate-pulse"></span>
                  <span className="text-xs font-bold text-[#E7ECF3]">{camera.name}</span>
                  <span className="text-[10px] font-mono text-[#8B95A7] bg-[#232C3D] px-1.5 py-0.5 rounded">
                    {camera.zone}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-[#3DA9FC]">1080p • 25 FPS</span>
                </div>
              </div>

              {/* Simulated Camera Video Surface with Detection Overlays */}
              <div className="relative aspect-video bg-[#05070B] flex items-center justify-center overflow-hidden">
                {/* Simulated CCTV Background */}
                <div className="absolute inset-0 opacity-40 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]"></div>
                
                {/* CCTV Timestamp & Watermark */}
                <div className="absolute top-2 left-2 text-[10px] font-mono text-[#8B95A7] bg-black/60 px-2 py-0.5 rounded">
                  CAM_0{idx+1} • {camera.location}
                </div>
                <div className="absolute top-2 right-2 text-[10px] font-mono text-[#34C77B] bg-black/60 px-2 py-0.5 rounded flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#34C77B]"></span>
                  LIVE
                </div>

                {/* Simulated Person & Bounding Overlays */}
                <div className="relative z-10 w-full h-full flex items-center justify-center p-6">
                  {/* Bounding Box 1: Normal Person Detection (Green) */}
                  <div className="absolute left-[20%] top-[25%] w-[24%] h-[60%] border-2 border-[#34C77B]/80 rounded bg-[#34C77B]/10 flex flex-col justify-between p-1.5">
                    <span className="text-[9px] font-mono font-bold bg-[#34C77B] text-black px-1 rounded w-fit">
                      PERSON 98%
                    </span>
                    <span className="text-[8px] font-mono text-[#34C77B] bg-black/70 px-1 rounded w-fit">
                      COMPLIANT
                    </span>
                  </div>

                  {/* Bounding Box 2: Compliance Flag (Amber) */}
                  <div className="absolute right-[22%] top-[20%] w-[26%] h-[65%] border-2 border-[#E8A33D] rounded bg-[#E8A33D]/10 flex flex-col justify-between p-1.5">
                    <span className="text-[9px] font-mono font-bold bg-[#E8A33D] text-black px-1 rounded w-fit">
                      FLAG: UNTUCKED 86%
                    </span>
                    <div className="flex items-center justify-between text-[8px] font-mono text-[#E8A33D] bg-black/80 p-0.5 rounded">
                      <span>MATCH: STU-2024</span>
                      <span className="text-[#3DA9FC]">91%</span>
                    </div>
                  </div>
                </div>

                {/* Footer overlay */}
                <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-[10px] font-mono text-[#8B95A7] bg-black/70 px-2.5 py-1 rounded">
                  <span>CADENCE: {camera.sampling_interval_seconds}s</span>
                  <span>BURST DETECTIONS: 2 SUBJECTS</span>
                </div>
              </div>

              {/* Camera Actions Footer */}
              <div className="p-2.5 bg-[#131A26] border-t border-[#232C3D] flex items-center justify-between text-xs">
                <span className="text-[11px] text-[#8B95A7] font-mono truncate max-w-[200px]">
                  {camera.stream_url || 'simulated://live'}
                </span>
                <button
                  onClick={() => handleSimulateFeed(camera.id)}
                  disabled={simulating === camera.id}
                  className="flex items-center gap-1 px-2.5 py-1 bg-[#232C3D] hover:bg-[#3DA9FC]/20 hover:text-[#3DA9FC] text-[#E7ECF3] rounded text-[11px] font-mono transition-colors"
                >
                  <Play className="w-3 h-3" />
                  <span>{simulating === camera.id ? 'SAMPLING...' : 'SIMULATE INGEST'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
