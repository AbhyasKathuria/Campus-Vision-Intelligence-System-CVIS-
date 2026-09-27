import React, { useState, useEffect } from 'react';
import { 
  Camera as CameraIcon, Plus, Video, Radio, 
  RefreshCw, CheckCircle, Upload, Settings 
} from 'lucide-react';
import { api } from '../../services/api';
import { Camera } from '../../types';

export const OpsCameraRegistry: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);

  // New Camera Form State
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [zone, setZone] = useState('');
  const [streamUrl, setStreamUrl] = useState('');
  const [cadence, setCadence] = useState(2.0);

  // Upload Recording State
  const [uploadCameraId, setUploadCameraId] = useState<string | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadCameras = async () => {
    try {
      setLoading(true);
      const data = await api.listCameras();
      setCameras(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCameras();
  }, []);

  const handleAddCamera = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCamera({
        name,
        location,
        zone,
        stream_url: streamUrl || undefined,
        sampling_interval_seconds: cadence,
        active: true
      });
      setShowAddModal(false);
      setName('');
      setLocation('');
      setZone('');
      setStreamUrl('');
      await loadCameras();
    } catch (err: any) {
      alert(err.message || 'Failed to add camera');
    }
  };

  const handleUploadRecording = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadCameraId || !videoFile) return;
    try {
      setUploading(true);
      // Upload recording to camera
      const formData = new FormData();
      formData.append('file', videoFile);
      formData.append('sampling_interval', cadence.toString());
      const res = await fetch(`/api/v1/cameras/${uploadCameraId}/recordings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('cvis_token')}`
        },
        body: formData
      });
      const rec = await res.json();
      
      // Trigger processing
      await fetch(`/api/v1/compliance/process-recording/${rec.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('cvis_token')}`
        }
      });

      alert(`Recording processed! Frames sampled at ${cadence}s cadence.`);
      setUploadCameraId(null);
      setVideoFile(null);
    } catch (err: any) {
      alert(err.message || 'Processing failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-[#E7ECF3] flex items-center gap-2">
            <CameraIcon className="w-5 h-5 text-[#3DA9FC]" />
            <span>Camera Registry & Stream Configuration</span>
          </h2>
          <p className="text-xs text-[#8B95A7]">
            Register RTSP/HLS feeds, configure frame extraction cadences, and upload recorded footage.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors shadow-lg shadow-[#3DA9FC]/20"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Camera</span>
        </button>
      </div>

      {/* Cameras Table */}
      <div className="bg-[#131A26] border border-[#232C3D] rounded-xl overflow-hidden">
        <div className="p-4 bg-[#0B0F17] border-b border-[#232C3D] flex items-center justify-between text-xs font-semibold text-[#8B95A7]">
          <span>Connected Sensors ({cameras.length})</span>
          <button onClick={loadCameras} className="p-1 hover:text-[#E7ECF3]">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0F17]/50 text-[#8B95A7] font-mono uppercase text-[10px] border-b border-[#232C3D]">
              <tr>
                <th className="p-3">Camera Name</th>
                <th className="p-3">Location</th>
                <th className="p-3">Zone</th>
                <th className="p-3">Sampling Cadence</th>
                <th className="p-3">Stream Protocol</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232C3D] font-mono">
              {cameras.map((cam) => (
                <tr key={cam.id} className="hover:bg-[#0B0F17]/50 transition-colors">
                  <td className="p-3 font-sans font-semibold text-[#E7ECF3]">
                    <div className="flex items-center gap-2">
                      <CameraIcon className="w-4 h-4 text-[#3DA9FC]" />
                      <span>{cam.name}</span>
                    </div>
                  </td>
                  <td className="p-3 text-[#8B95A7] font-sans">{cam.location}</td>
                  <td className="p-3 text-[#3DA9FC]">{cam.zone}</td>
                  <td className="p-3 text-[#E7ECF3]">1 frame / {cam.sampling_interval_seconds}s</td>
                  <td className="p-3 text-[#8B95A7] truncate max-w-[150px]">{cam.stream_url || 'RTSP (Internal)'}</td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#34C77B]/10 text-[#34C77B] text-[10px] font-bold">
                      <Radio className="w-3 h-3 animate-pulse" />
                      <span>ONLINE</span>
                    </span>
                  </td>
                  <td className="p-3 text-right font-sans">
                    <button
                      onClick={() => setUploadCameraId(cam.id)}
                      className="px-2.5 py-1 bg-[#232C3D] hover:bg-[#3DA9FC]/20 hover:text-[#3DA9FC] text-[#E7ECF3] rounded text-[11px] font-medium transition-colors"
                    >
                      Feed Video
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Camera Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-[#131A26] border border-[#232C3D] w-full max-w-md rounded-xl p-5 shadow-2xl">
            <h3 className="text-sm font-bold text-[#E7ECF3] mb-4">Register Camera Sensor</h3>
            <form onSubmit={handleAddCamera} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Camera Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Science Lab 3 East"
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Physical Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Science Complex Level 2"
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Campus Zone</label>
                <input
                  type="text"
                  value={zone}
                  onChange={(e) => setZone(e.target.value)}
                  placeholder="e.g. Science Block, Library, Hostel"
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Stream URL (RTSP / HLS)</label>
                <input
                  type="text"
                  value={streamUrl}
                  onChange={(e) => setStreamUrl(e.target.value)}
                  placeholder="rtsp://admin:pass@192.168.1.10:554/live"
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Frame Sampling Interval (Seconds)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="10.0"
                  value={cadence}
                  onChange={(e) => setCadence(parseFloat(e.target.value))}
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] font-mono focus:border-[#3DA9FC] focus:outline-none"
                />
                <span className="text-[10px] text-[#8B95A7] mt-1 block">Default 2.0s = 0.5 FPS (eliminates CPU/GPU waste).</span>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 bg-[#232C3D] hover:bg-[#232C3D]/80 text-[#E7ECF3] text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors"
                >
                  Register
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Video Modal */}
      {uploadCameraId && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-[#131A26] border border-[#232C3D] w-full max-w-md rounded-xl p-5 shadow-2xl">
            <h3 className="text-sm font-bold text-[#E7ECF3] mb-2">Ingest Footage to Camera</h3>
            <p className="text-xs text-[#8B95A7] mb-4">
              Upload a recorded CCTV clip (<code className="text-[#3DA9FC]">.mp4</code>). Frames will be sampled at the configured cadence for compliance review.
            </p>

            <form onSubmit={handleUploadRecording} className="space-y-4">
              <div className="border border-[#232C3D] rounded-lg p-4 bg-[#0B0F17]">
                <input
                  type="file"
                  accept="video/mp4,video/webm"
                  onChange={(e) => setVideoFile(e.target.files ? e.target.files[0] : null)}
                  required
                  className="text-xs text-[#8B95A7]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadCameraId(null)}
                  className="px-3 py-1.5 bg-[#232C3D] hover:bg-[#232C3D]/80 text-[#E7ECF3] text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!videoFile || uploading}
                  className="px-4 py-1.5 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors disabled:opacity-50"
                >
                  {uploading ? 'Processing Frames...' : 'Process Video'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
