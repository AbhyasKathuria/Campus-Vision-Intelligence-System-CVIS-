import React, { useState, useEffect } from 'react';
import { 
  Image as ImageIcon, Upload, Plus, Calendar, 
  FolderPlus, RefreshCw, CheckCircle, FileArchive, Users, Sparkles, UserX 
} from 'lucide-react';
import { api } from '../../services/api';
import { Event, EventPhoto, UnknownFaceCluster } from '../../types';

export const OpsEventPhotoManager: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [photos, setPhotos] = useState<EventPhoto[]>([]);
  const [clusters, setClusters] = useState<UnknownFaceCluster[]>([]);
  const [activeTab, setActiveTab] = useState<'photos' | 'clusters'>('photos');
  const [loading, setLoading] = useState(true);
  const [photosLoading, setPhotosLoading] = useState(false);
  const [clustersLoading, setClustersLoading] = useState(false);

  // New Event Form State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [eventName, setEventName] = useState('');
  const [eventDate, setEventDate] = useState(new Date().toISOString().split('T')[0]);
  const [eventDesc, setEventDesc] = useState('');

  // Bulk Upload State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any | null>(null);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await api.listEvents();
      setEvents(data);
      if (data.length > 0 && !selectedEvent) {
        setSelectedEvent(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadPhotos = async (eventId: string) => {
    try {
      setPhotosLoading(true);
      const data = await api.listEventPhotos(eventId);
      setPhotos(data);
    } catch (e) {
      console.error(e);
    } finally {
      setPhotosLoading(false);
    }
  };

  const loadClusters = async (eventId: string) => {
    try {
      setClustersLoading(true);
      const data = await api.listUnknownClusters(eventId);
      setClusters(data);
    } catch (e) {
      console.error(e);
    } finally {
      setClustersLoading(false);
    }
  };

  const handleRunClustering = async () => {
    if (!selectedEvent) return;
    try {
      setClustersLoading(true);
      const data = await api.clusterUnknownFaces(selectedEvent.id);
      setClusters(data);
      setActiveTab('clusters');
    } catch (err: any) {
      alert(err.message || 'Clustering failed');
    } finally {
      setClustersLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    if (selectedEvent) {
      loadPhotos(selectedEvent.id);
      loadClusters(selectedEvent.id);
    }
  }, [selectedEvent]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await api.createEvent({
        name: eventName,
        date: eventDate,
        description: eventDesc
      });
      setShowCreateModal(false);
      setEventName('');
      setEventDesc('');
      await loadEvents();
      setSelectedEvent(created);
    } catch (err: any) {
      alert(err.message || 'Failed to create event');
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !selectedEvent) return;
    try {
      setUploading(true);
      setUploadResult(null);
      const result = await api.uploadEventPhotos(selectedEvent.id, uploadFile);
      setUploadResult(result);
      setUploadFile(null);
      await loadPhotos(selectedEvent.id);
      await loadEvents();
    } catch (err: any) {
      alert(err.message || 'Upload failed');
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
            <ImageIcon className="w-5 h-5 text-[#3DA9FC]" />
            <span>Event Photo Corpus Management</span>
          </h2>
          <p className="text-xs text-[#8B95A7]">
            Bulk ingest, extract multi-face embeddings, and build the vector search index for the student photo finder.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors shadow-lg shadow-[#3DA9FC]/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Campus Event</span>
        </button>
      </div>

      {/* Main Grid: Events List & Upload/Gallery Pane */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Events List (4 cols) */}
        <div className="lg:col-span-4 bg-[#131A26] border border-[#232C3D] rounded-xl overflow-hidden flex flex-col max-h-[calc(100vh-220px)]">
          <div className="p-3 bg-[#0B0F17] border-b border-[#232C3D] flex items-center justify-between text-xs font-semibold text-[#8B95A7]">
            <span>Events ({events.length})</span>
            <button onClick={loadEvents} className="p-1 hover:text-[#E7ECF3]">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="overflow-y-auto divide-y divide-[#232C3D] flex-1">
            {events.map((ev) => {
              const isSelected = selectedEvent?.id === ev.id;
              return (
                <div
                  key={ev.id}
                  onClick={() => setSelectedEvent(ev)}
                  className={`p-3.5 cursor-pointer transition-colors ${
                    isSelected ? 'bg-[#3DA9FC]/10 border-l-2 border-[#3DA9FC]' : 'hover:bg-[#0B0F17]/60'
                  }`}
                >
                  <p className="text-xs font-bold text-[#E7ECF3]">{ev.name}</p>
                  <p className="text-[11px] text-[#8B95A7] mt-0.5 line-clamp-1">{ev.description || 'No description'}</p>
                  <div className="flex items-center justify-between mt-2 text-[10px] font-mono text-[#8B95A7]">
                    <span>{ev.date}</span>
                    <span className="text-[#3DA9FC]">{ev.photo_count || 0} photos</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Ingestion & Album Gallery (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {selectedEvent ? (
            <>
              {/* Bulk Ingestion Zone */}
              <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-5">
                <h3 className="text-xs font-bold text-[#E7ECF3] uppercase tracking-wider mb-2">
                  Bulk Upload Photos to "{selectedEvent.name}"
                </h3>
                <p className="text-xs text-[#8B95A7] mb-4">
                  Supports individual images (<code className="text-[#3DA9FC]">.jpg, .png</code>) or full archives (<code className="text-[#3DA9FC]">.zip</code> up to 500MB). Faces are automatically detected and indexed into FAISS.
                </p>

                <form onSubmit={handleUploadSubmit} className="space-y-4">
                  <div className="border-2 border-dashed border-[#232C3D] hover:border-[#3DA9FC]/50 rounded-xl p-6 text-center transition-colors">
                    <input
                      type="file"
                      id="bulk-upload-input"
                      accept=".jpg,.jpeg,.png,.webp,.zip"
                      onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                      className="hidden"
                    />
                    <label htmlFor="bulk-upload-input" className="cursor-pointer flex flex-col items-center">
                      <div className="w-12 h-12 rounded-full bg-[#0B0F17] border border-[#232C3D] flex items-center justify-center text-[#3DA9FC] mb-2">
                        <Upload className="w-6 h-6" />
                      </div>
                      <span className="text-xs font-semibold text-[#E7ECF3]">
                        {uploadFile ? uploadFile.name : 'Click to select individual photos or a .ZIP archive'}
                      </span>
                      <span className="text-[10px] text-[#8B95A7] mt-1">
                        Max upload size: 500MB • Pre-computes 512-dim face embeddings automatically
                      </span>
                    </label>
                  </div>

                  {uploadResult && (
                    <div className="p-3 bg-[#34C77B]/10 border border-[#34C77B]/30 rounded-lg flex items-center gap-2 text-xs text-[#34C77B]">
                      <CheckCircle className="w-4 h-4 shrink-0" />
                      <span>{uploadResult.message}</span>
                    </div>
                  )}

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={!uploadFile || uploading}
                      className="flex items-center gap-2 px-5 py-2 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Upload className="w-3.5 h-3.5" />
                      <span>{uploading ? 'Processing & Indexing Faces...' : 'Start Ingestion'}</span>
                    </button>
                  </div>
                </form>
              </div>

              {/* Gallery & Clusters Pane */}
              <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setActiveTab('photos')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase transition-colors ${
                        activeTab === 'photos'
                          ? 'bg-[#3DA9FC] text-[#0B0F17] font-bold'
                          : 'bg-[#0B0F17] border border-[#232C3D] text-[#8B95A7] hover:text-[#E7ECF3]'
                      }`}
                    >
                      Photos in Album ({photos.length})
                    </button>
                    <button
                      onClick={() => setActiveTab('clusters')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase transition-colors flex items-center gap-1.5 ${
                        activeTab === 'clusters'
                          ? 'bg-[#E8A33D] text-[#0B0F17] font-bold'
                          : 'bg-[#0B0F17] border border-[#232C3D] text-[#8B95A7] hover:text-[#E7ECF3]'
                      }`}
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Unidentified Face Clusters ({clusters.length})</span>
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleRunClustering}
                      disabled={clustersLoading || photos.length === 0}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-[#0B0F17] border border-[#232C3D] hover:bg-[#232C3D] text-[#E8A33D] rounded-lg transition-colors disabled:opacity-50"
                      title="Run pairwise cosine clustering on all non-enrolled event faces"
                    >
                      <Sparkles className={`w-3.5 h-3.5 ${clustersLoading ? 'animate-spin' : ''}`} />
                      <span>{clustersLoading ? 'Clustering...' : 'Cluster Unidentified Faces'}</span>
                    </button>

                    <button 
                      onClick={() => {
                        if (selectedEvent) {
                          loadPhotos(selectedEvent.id);
                          loadClusters(selectedEvent.id);
                        }
                      }}
                      className="p-1.5 bg-[#0B0F17] border border-[#232C3D] text-[#8B95A7] hover:text-[#E7ECF3] rounded-lg"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${(photosLoading || clustersLoading) ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                </div>

                {activeTab === 'photos' ? (
                  photos.length === 0 ? (
                    <div className="p-12 text-center text-[#8B95A7] text-xs">
                      No photos uploaded to this event yet.
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                      {photos.map((p) => (
                        <div key={p.id} className="group relative aspect-square bg-[#0B0F17] rounded-lg overflow-hidden border border-[#232C3D]">
                          <img 
                            src={`/media/${p.thumbnail_ref || p.storage_ref}`} 
                            alt="Event item" 
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-2 text-[10px] font-mono text-[#E7ECF3]">
                            <span className="flex items-center gap-1 text-[#3DA9FC]">
                              <Users className="w-3 h-3" />
                              <span>{p.face_count} faces indexed</span>
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                ) : (
                  clusters.length === 0 ? (
                    <div className="p-12 text-center text-[#8B95A7] text-xs space-y-2">
                      <UserX className="w-8 h-8 mx-auto text-[#8B95A7]/40" />
                      <p>No unidentified face clusters generated yet.</p>
                      <p className="text-[11px] text-[#8B95A7]/60">Click "Cluster Unidentified Faces" to group recurrent non-enrolled attendees across event photos.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                      {clusters.map((c) => (
                        <div key={c.id} className="p-3 bg-[#0B0F17] border border-[#232C3D] rounded-xl flex items-center gap-3 hover:border-[#E8A33D]/50 transition-colors">
                          <div className="w-14 h-14 rounded-lg bg-[#131A26] border border-[#232C3D] overflow-hidden shrink-0">
                            {c.representative_crop_ref ? (
                              <img
                                src={`/media/${c.representative_crop_ref}`}
                                alt={c.cluster_label}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-[#8B95A7]">
                                <Users className="w-6 h-6" />
                              </div>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-xs font-bold text-[#E7ECF3] truncate">{c.cluster_label}</h4>
                            <div className="flex items-center gap-1.5 mt-1">
                              <span className="px-2 py-0.5 rounded bg-[#E8A33D]/15 text-[#E8A33D] font-mono text-[10px] font-bold">
                                {c.face_count} photos appeared
                              </span>
                            </div>
                            <p className="text-[10px] text-[#8B95A7] mt-1 truncate">
                              Cosine distance cluster
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                )}
              </div>
            </>
          ) : (
            <div className="bg-[#131A26] border border-[#232C3D] rounded-xl p-12 text-center text-[#8B95A7] text-xs">
              Select or create an event to manage photos.
            </div>
          )}
        </div>
      </div>

      {/* Create Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-[#131A26] border border-[#232C3D] w-full max-w-md rounded-xl p-5 shadow-2xl">
            <h3 className="text-sm font-bold text-[#E7ECF3] mb-4">Create New Campus Event</h3>
            <form onSubmit={handleCreateEvent} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Event Name</label>
                <input
                  type="text"
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                  placeholder="e.g. Convocation 2026"
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Date</label>
                <input
                  type="date"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  required
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#8B95A7] mb-1">Description (Optional)</label>
                <textarea
                  rows={3}
                  value={eventDesc}
                  onChange={(e) => setEventDesc(e.target.value)}
                  placeholder="e.g. Annual graduation ceremony photo sets."
                  className="w-full bg-[#0B0F17] border border-[#232C3D] rounded-lg px-3 py-2 text-xs text-[#E7ECF3] focus:border-[#3DA9FC] focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 bg-[#232C3D] hover:bg-[#232C3D]/80 text-[#E7ECF3] text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-[#3DA9FC] hover:bg-[#3DA9FC]/80 text-[#0B0F17] text-xs font-bold rounded-lg transition-colors"
                >
                  Create Event
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
