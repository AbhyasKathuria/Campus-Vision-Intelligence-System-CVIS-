import React, { useState } from 'react';
import { 
  Camera, Upload, Download, Sparkles, AlertCircle, 
  CheckCircle, ArrowRight, Eye, RefreshCw 
} from 'lucide-react';
import { api } from '../../services/api';
import { PhotoMatchItem } from '../../types';

export const StudentSelfieSearch: React.FC = () => {
  const [selfieFile, setSelfieFile] = useState<File | null>(null);
  const [selfiePreview, setSelfiePreview] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [matches, setMatches] = useState<PhotoMatchItem[] | null>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoMatchItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (file: File | null) => {
    if (!file) return;
    setSelfieFile(file);
    const reader = new FileReader();
    reader.onload = () => setSelfiePreview(reader.result as string);
    reader.readAsDataURL(file);
    setError(null);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selfieFile) return;

    try {
      setSearching(true);
      setError(null);
      const res = await api.searchSelfie(selfieFile);
      setMatches(res.matches);
    } catch (err: any) {
      setError(err.message || 'Search failed. Please try another photo.');
    } finally {
      setSearching(false);
    }
  };

  const resetSearch = () => {
    setSelfieFile(null);
    setSelfiePreview(null);
    setMatches(null);
    setError(null);
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#0D9488]/10 text-[#0D9488] text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Self-Service Event Photo Finder</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Find all your campus photos in seconds.
        </h1>
        <p className="text-sm text-slate-600">
          Upload a quick selfie, and our private face recognition engine will search every university event gallery for photos of you.
        </p>
      </div>

      {/* Selfie Upload / Search Card */}
      {!matches ? (
        <div className="max-w-md mx-auto bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <form onSubmit={handleSearch} className="space-y-5">
            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="border-2 border-dashed border-slate-200 hover:border-[#0D9488] rounded-xl p-6 text-center transition-colors">
              <input
                type="file"
                id="student-selfie-input"
                accept="image/*"
                onChange={(e) => handleFileChange(e.target.files ? e.target.files[0] : null)}
                className="hidden"
              />
              <label htmlFor="student-selfie-input" className="cursor-pointer flex flex-col items-center">
                {selfiePreview ? (
                  <div className="relative w-36 h-36 rounded-full overflow-hidden border-4 border-[#0D9488]/20 mb-3 shadow-inner">
                    <img src={selfiePreview} alt="Selfie preview" className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="w-16 h-16 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center text-[#0D9488] mb-3">
                    <Camera className="w-8 h-8" />
                  </div>
                )}
                <span className="text-sm font-semibold text-slate-900">
                  {selfieFile ? 'Change Selfie' : 'Take or upload a selfie'}
                </span>
                <span className="text-xs text-slate-500 mt-1">
                  JPG or PNG up to 10MB
                </span>
              </label>
            </div>

            {/* Privacy Guarantee Card */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-600 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-[#0D9488] shrink-0" />
              <span>
                <strong>Privacy Guaranteed:</strong> Your selfie is processed purely in-memory to find your photos and is never saved.
              </span>
            </div>

            <button
              type="submit"
              disabled={!selfieFile || searching}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[#0D9488] hover:bg-[#0F766E] text-white font-bold text-sm rounded-xl transition-colors shadow-lg shadow-[#0D9488]/20 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{searching ? 'Searching Campus Albums...' : 'Find My Photos'}</span>
            </button>
          </form>
        </div>
      ) : (
        /* Results Gallery */
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                {matches.length > 0 ? `We found ${matches.length} photo(s) of you!` : "No matching photos found"}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Click any photo to view full size and download.
              </p>
            </div>

            <button
              onClick={resetSearch}
              className="flex items-center gap-1.5 px-4 py-2 border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Try Another Selfie</span>
            </button>
          </div>

          {matches.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                <Camera className="w-8 h-8" />
              </div>
              <p className="text-sm font-semibold text-slate-800">
                Not seeing yourself?
              </p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Try uploading a selfie with better lighting, looking straight at the camera without dark sunglasses or strong glare.
              </p>
              <button
                onClick={resetSearch}
                className="px-5 py-2.5 bg-[#0D9488] text-white text-xs font-bold rounded-lg shadow"
              >
                Upload New Photo
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {matches.map((item) => (
                <div
                  key={item.photo_id}
                  onClick={() => setSelectedPhoto(item)}
                  className="group relative aspect-square bg-slate-100 rounded-xl overflow-hidden cursor-pointer border border-slate-200 hover:shadow-md transition-shadow"
                >
                  <img
                    src={`/media/${item.thumbnail_ref || item.storage_ref}`}
                    alt="Campus event match"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-between p-3">
                    <span className="text-xs font-semibold text-white">View Full Photo</span>
                    <a
                      href={`/media/${item.storage_ref}`}
                      download
                      onClick={(e) => e.stopPropagation()}
                      className="p-1.5 bg-white/90 hover:bg-white text-slate-900 rounded-lg transition-colors"
                      title="Download Photo"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Full Photo Modal */}
      {selectedPhoto && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-3xl w-full overflow-hidden shadow-2xl flex flex-col">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <span className="text-sm font-bold text-slate-900">Event Photo</span>
              <div className="flex items-center gap-2">
                <a
                  href={`/media/${selectedPhoto.storage_ref}`}
                  download
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0D9488] text-white text-xs font-bold rounded-lg shadow"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download High-Res</span>
                </a>
                <button
                  onClick={() => setSelectedPhoto(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="max-h-[70vh] bg-black flex items-center justify-center overflow-hidden">
              <img
                src={`/media/${selectedPhoto.storage_ref}`}
                alt="Selected match"
                className="max-h-full max-w-full object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
