import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  UploadCloud, 
  FileText, 
  Image as ImageIcon, 
  FileIcon, 
  Trash2, 
  CheckCircle2, 
  AlertTriangle, 
  Download, 
  Loader2, 
  Sparkles, 
  RefreshCw,
  Lock,
  Mail,
  LogOut,
  UserCheck,
  FileSpreadsheet,
  Settings
} from 'lucide-react';

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default function App() {
  // Authentication State
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail') || '');
  const [authTab, setAuthTab] = useState('login');
  const [emailInput, setEmailInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [authSuccess, setAuthSuccess] = useState(null);

  // API URL Settings & Health Check
  const [showSettings, setShowSettings] = useState(false);
  const [backendUrl, setBackendUrl] = useState(localStorage.getItem('backend_api_url') || 'https://compressor-and-convertor.onrender.com');
  const [serverStatus, setServerStatus] = useState('checking');

  const getApiBaseUrl = () => {
    const saved = localStorage.getItem('backend_api_url');
    if (saved) return saved;
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return '';
    }
    return 'https://compressor-and-convertor.onrender.com';
  };

  useEffect(() => {
    let active = true;
    const checkServer = async () => {
      setServerStatus('checking');
      const baseUrl = getApiBaseUrl() || 'http://127.0.0.1:8000';
      try {
        const res = await axios.get(`${baseUrl}/`, { timeout: 8000 });
        if (active) {
          if (res.data && res.data.status === 'healthy') {
            setServerStatus('online');
          } else {
            setServerStatus('offline');
          }
        }
      } catch (err) {
        if (active) {
          setServerStatus('offline');
        }
      }
    };
    checkServer();
    return () => { active = false; };
  }, [backendUrl]);

  // Compressor State
  const [files, setFiles] = useState([]);
  const [quality, setQuality] = useState(80);
  const [archiveFormat, setArchiveFormat] = useState('zip');
  const [isDragging, setIsDragging] = useState(false);
  const [compressing, setCompressing] = useState(false);
  const [compressedResult, setCompressedResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Format conversion and Target size optimization states
  const [targetFormat, setTargetFormat] = useState(''); // empty = Keep Original
  const [optimizeSize, setOptimizeSize] = useState(false);
  const [sizePreset, setSizePreset] = useState('under_1mb');
  const [customMin, setCustomMin] = useState(0);
  const [customMax, setCustomMax] = useState(1);
  const [customMinUnit, setCustomMinUnit] = useState('MB');
  const [customMaxUnit, setCustomMaxUnit] = useState('MB');

  // File Format Conversion states
  const [conversionType, setConversionType] = useState(''); // empty = compression mode
  const [targetImgFormat, setTargetImgFormat] = useState('PNG');
  
  const fileInputRef = useRef(null);
  
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      localStorage.setItem('userEmail', userEmail);
    } else {
      localStorage.removeItem('token');
      localStorage.removeItem('userEmail');
    }
  }, [token, userEmail]);

  // Check file types in uploaded lists
  const getFileExtension = (name) => name.split('.').pop().toLowerCase();
  
  const hasImages = files.some(f => {
    return ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'].includes(getFileExtension(f.name));
  });

  const allImages = files.length > 0 && files.every(f => {
    return ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'].includes(getFileExtension(f.name));
  });

  const isSinglePdf = files.length === 1 && getFileExtension(files[0].name) === 'pdf';
  const isSingleDocx = files.length === 1 && getFileExtension(files[0].name) === 'docx';

  // Automatically reset or set conversion type presets on file changes
  useEffect(() => {
    if (files.length === 0) {
      setConversionType('');
    } else if (allImages && conversionType === '') {
      // Don't auto-set to conversion, keep it compression by default
    }
  }, [files, allImages]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFilesList) => {
    setError(null);
    setCompressedResult(null);

    const formatted = newFilesList.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      name: file.name,
      size: file.size,
      status: 'idle',
      progress: 0,
      backendId: null,
      error: null
    }));
    setFiles(prev => [...prev, ...formatted]);
  };

  const removeFile = (id) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError(null);
    setAuthSuccess(null);
    setAuthLoading(true);

    if (!emailInput || !passwordInput) {
      setAuthError('Please fill in all fields.');
      setAuthLoading(false);
      return;
    }

    if (passwordInput.length < 8) {
      setAuthError('Password must be at least 8 characters long.');
      setAuthLoading(false);
      return;
    }

    try {
      if (authTab === 'signup') {
        const response = await axios.post(`${getApiBaseUrl()}/api/signup`, {
          email: emailInput,
          password: passwordInput
        });
        setAuthSuccess(response.data.message);
        setAuthTab('login');
        setPasswordInput('');
      } else {
        const response = await axios.post(`${getApiBaseUrl()}/api/login`, {
          email: emailInput,
          password: passwordInput
        });
        setToken(response.data.token);
        setUserEmail(emailInput);
        setEmailInput('');
        setPasswordInput('');
      }
    } catch (err) {
      setAuthError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSignOut = () => {
    setToken('');
    setUserEmail('');
    setFiles([]);
    setCompressedResult(null);
    setError(null);
  };

  const uploadSingleFile = async (fileItem) => {
    setFiles(prev => prev.map(f => f.id === fileItem.id ? { ...f, status: 'uploading', progress: 0 } : f));
    
    const formData = new FormData();
    formData.append('file', fileItem.file);

    try {
      const response = await axios.post(`${getApiBaseUrl()}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setFiles(prev => prev.map(f => f.id === fileItem.id ? { ...f, progress: percentCompleted } : f));
        }
      });

      setFiles(prev => prev.map(f => f.id === fileItem.id ? { 
        ...f, 
        status: 'uploaded', 
        backendId: response.data.file_id 
      } : f));
      
      return response.data.file_id;
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Upload failed';
      setFiles(prev => prev.map(f => f.id === fileItem.id ? { 
        ...f, 
        status: 'failed', 
        error: errMsg 
      } : f));
      throw new Error(errMsg);
    }
  };

  const handleAction = async () => {
    if (files.length === 0) return;
    setError(null);
    setCompressedResult(null);
    setCompressing(true);

    try {
      // 1. Upload files
      const uploadPromises = files.map(async (f) => {
        if (f.status === 'uploaded' && f.backendId) {
          return f.backendId;
        }
        return await uploadSingleFile(f);
      });

      const backendIds = await Promise.all(uploadPromises);
      
      if (conversionType !== '') {
        // Run conversion endpoint
        const convertResponse = await axios.post(`${getApiBaseUrl()}/api/convert`, {
          file_ids: backendIds,
          conversion_type: conversionType,
          target_img_format: targetImgFormat
        }, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        setCompressedResult(convertResponse.data);
      } else {
        // Run compression endpoint
        let minBytes = 0;
        let maxBytes = 0;
        
        if (optimizeSize) {
          if (sizePreset === 'under_500kb') {
            maxBytes = 500 * 1024;
          } else if (sizePreset === 'under_1mb') {
            maxBytes = 1024 * 1024;
          } else if (sizePreset === '1mb_2mb') {
            minBytes = 1024 * 1024;
            maxBytes = 2 * 1024 * 1024;
          } else if (sizePreset === '2mb_5mb') {
            minBytes = 2 * 1024 * 1024;
            maxBytes = 5 * 1024 * 1024;
          } else if (sizePreset === 'custom') {
            const minMultiplier = customMinUnit === 'MB' ? 1024 * 1024 : 1024;
            const maxMultiplier = customMaxUnit === 'MB' ? 1024 * 1024 : 1024;
            minBytes = Math.round(customMin * minMultiplier);
            maxBytes = Math.round(customMax * maxMultiplier);
          }
        }

        const compressResponse = await axios.post(`${getApiBaseUrl()}/api/compress`, {
          file_ids: backendIds,
          quality: Number(quality),
          archive_format: archiveFormat,
          optimize_size: optimizeSize,
          target_min_size: minBytes,
          target_max_size: maxBytes,
          target_format: targetFormat || null
        }, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        setCompressedResult(compressResponse.data);
      }
      
      setFiles(prev => prev.map(f => ({ ...f, status: 'idle', progress: 0, backendId: null })));
    } catch (err) {
      console.error(err);
      if (err.response?.status === 401 || err.response?.status === 403) {
        handleSignOut();
        setAuthError('Your session has expired. Please log in again.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Operation failed.');
      }
    } finally {
      setCompressing(false);
    }
  };

  const handleDownload = () => {
    if (!compressedResult) return;
    window.location.href = `${getApiBaseUrl()}/api/download/${compressedResult.download_id}`;
    setCompressedResult(null);
    setFiles([]);
  };

  const getFileIcon = (filename) => {
    const ext = getFileExtension(filename);
    if (['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'].includes(ext)) {
      return <ImageIcon className="w-5 h-5 text-emerald-400" />;
    }
    if (ext === 'pdf') {
      return <FileText className="w-5 h-5 text-red-400" />;
    }
    if (ext === 'docx') {
      return <FileIcon className="w-5 h-5 text-blue-400" />;
    }
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
      return <FileIcon className="w-5 h-5 text-amber-400" />;
    }
    return <FileIcon className="w-5 h-5 text-indigo-400" />;
  };

  const totalOriginalSize = files.reduce((acc, f) => acc + f.size, 0);

  // Check if we can display conversion tools
  const canConvert = allImages || isSinglePdf || isSingleDocx;

  return (
    <div className="relative min-h-screen bg-[#090D16] bg-grid-pattern text-[#F3F4F6] flex flex-col justify-between overflow-x-hidden">
      
      {/* Ambient backgrounds */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-[#2563EB]/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-[#00F2FE]/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="border-b border-white/5 bg-[#090D16]/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#2563EB] to-[#00F2FE] flex items-center justify-center shadow-lg shadow-[#00F2FE]/10">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-[#FFFFFF] via-[#F3F4F6] to-[#9CA3AF] bg-clip-text text-transparent">
                ShrinkIO
              </h1>
              <p className="text-[10px] text-[#9CA3AF] font-semibold tracking-wider uppercase">
                Universal Compressor
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Server Status Pill */}
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold ${
              serverStatus === 'online'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                : serverStatus === 'offline'
                ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
            }`}>
              <span className={`w-2 h-2 rounded-full ${
                serverStatus === 'online'
                  ? 'bg-emerald-500 animate-pulse'
                  : serverStatus === 'offline'
                  ? 'bg-rose-500'
                  : 'bg-amber-500 animate-spin'
              }`} />
              <span className="hidden md:inline">Server: </span>
              <span className="capitalize">{serverStatus}</span>
            </div>

            {/* Settings Button */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-all cursor-pointer"
              title="API Configuration"
            >
              <Settings className="w-4 h-4" />
            </button>

            {token && (
              <>
                <div className="hidden sm:flex items-center gap-2 text-xs font-semibold bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-slate-300">
                  <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="truncate max-w-[120px]" title={userEmail}>{userEmail}</span>
                </div>
                <button
                  onClick={handleSignOut}
                  className="flex items-center gap-1.5 text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-xl hover:bg-rose-500 hover:text-white hover:border-rose-500 transition-all duration-300 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto px-6 py-12 flex-1 w-full flex items-center justify-center">
        
        {!token ? (
          /* Authentication Screen */
          <div className="w-full max-w-md glass rounded-3xl border border-slate-800/80 p-8 shadow-2xl relative overflow-hidden animate-in fade-in zoom-in-95 duration-300">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
            
            <div className="text-center mb-8">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-3">
                <Lock className="w-6 h-6 text-indigo-400" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-100">
                {authTab === 'login' ? 'Welcome Back' : 'Create Account'}
              </h2>
              <p className="text-xs text-slate-400 mt-1.5">
                {authTab === 'login' 
                  ? 'Sign in to access universal file & image compression tools.' 
                  : 'Register to start shrinking large images and files securely.'}
              </p>
            </div>

            <div className="grid grid-cols-2 p-1 bg-slate-900/80 rounded-xl border border-slate-800/60 mb-6">
              <button
                type="button"
                onClick={() => {
                  setAuthTab('login');
                  setAuthError(null);
                  setAuthSuccess(null);
                }}
                className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                  authTab === 'login' 
                    ? 'bg-indigo-500 text-white shadow-md' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setAuthTab('signup');
                  setAuthError(null);
                  setAuthSuccess(null);
                }}
                className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                  authTab === 'signup' 
                    ? 'bg-indigo-500 text-white shadow-md' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Register
              </button>
            </div>

            {authError && (
              <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-2.5 text-rose-400 text-xs mb-5">
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p className="leading-relaxed">{authError}</p>
              </div>
            )}
            {authSuccess && (
              <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-2.5 text-emerald-400 text-xs mb-5">
                <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p className="leading-relaxed">{authSuccess}</p>
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    placeholder="name@example.com"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-indigo-500 text-slate-200 transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-indigo-500 text-slate-200 transition-colors"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-3 px-4 mt-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white font-semibold text-sm shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {authLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : authTab === 'login' ? (
                  'Sign In'
                ) : (
                  'Create Account'
                )}
              </button>
            </form>
          </div>
        ) : (
          /* Dashboard Compressor UI */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start w-full">
            
            {/* Left Column: Drag & Drop + File List */}
            <div className="lg:col-span-7 space-y-6">
              
              {/* Drag & Drop Card */}
              <div 
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`glass glass-hover rounded-2xl p-8 border-2 border-dashed flex flex-col items-center justify-center text-center relative transition-all duration-300 min-h-[280px] group ${
                  isDragging 
                    ? 'border-indigo-500 bg-indigo-950/20 shadow-lg shadow-indigo-500/10' 
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <input 
                  type="file" 
                  onChange={handleFileSelect} 
                  multiple 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                />
                
                <div className="w-16 h-16 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:border-indigo-500/50 group-hover:bg-indigo-950/20 transition-all duration-300">
                  <UploadCloud className={`w-8 h-8 ${isDragging ? 'text-indigo-400 animate-bounce' : 'text-slate-400 group-hover:text-indigo-400'}`} />
                </div>

                <h3 className="text-lg font-semibold text-slate-200 mb-1">
                  Drag & drop files here
                </h3>
                <p className="text-sm text-slate-400 mb-4 max-w-xs">
                  Supports images (JPG, PNG, WebP), Word docs (.docx), PDFs, and data files.
                </p>
                
                <button 
                  type="button"
                  className="px-4 py-2 text-xs font-semibold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 rounded-lg group-hover:bg-indigo-500 group-hover:text-white group-hover:border-indigo-500 transition-all duration-300"
                >
                  Browse Files
                </button>
              </div>

              {/* Selected Files List */}
              {files.length > 0 && (
                <div className="glass rounded-2xl p-6 border border-slate-800/80 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
                    <h3 className="font-semibold text-slate-300 flex items-center gap-2">
                      Selected Files 
                      <span className="bg-slate-800 text-slate-400 text-xs px-2 py-0.5 rounded-full font-normal">
                        {files.length}
                      </span>
                    </h3>
                    <span className="text-xs text-slate-400">
                      Total: {formatSize(totalOriginalSize)}
                    </span>
                  </div>

                  <div className="max-h-[300px] overflow-y-auto space-y-3 pr-1">
                    {files.map((fileItem) => (
                      <div 
                        key={fileItem.id}
                        className="p-3 bg-slate-900/60 border border-slate-800/60 rounded-xl flex items-center justify-between gap-4 group hover:border-slate-700/60 transition-colors"
                      >
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                          <div className="flex-shrink-0">
                            {getFileIcon(fileItem.name)}
                          </div>
                          
                          <div className="min-w-0 flex-1">
                            <div className="flex items-baseline justify-between gap-2 mb-1">
                              <p className="text-xs font-medium text-slate-200 truncate pr-4" title={fileItem.name}>
                                {fileItem.name}
                              </p>
                              <span className="text-[10px] text-slate-500 flex-shrink-0">
                                {formatSize(fileItem.size)}
                              </span>
                            </div>

                            {fileItem.status === 'uploading' && (
                              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                <div 
                                  className="bg-gradient-to-r from-indigo-500 to-violet-600 h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${fileItem.progress}%` }}
                                />
                              </div>
                            )}

                            {fileItem.status === 'failed' && (
                              <span className="text-[10px] text-rose-400 flex items-center gap-1 font-medium mt-1">
                                <AlertTriangle className="w-3 h-3" />
                                {fileItem.error}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 flex-shrink-0">
                          {fileItem.status === 'uploaded' && (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          )}
                          
                          {fileItem.status === 'uploading' && (
                            <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                          )}

                          <button 
                            onClick={() => removeFile(fileItem.id)}
                            disabled={compressing}
                            className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/10 transition-colors disabled:opacity-30 disabled:pointer-events-none"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>

            {/* Right Column: Compression / Conversion Controls & Output */}
            <div className="lg:col-span-5 space-y-6">
              
              {/* Mode Selection Tab */}
              {canConvert && (
                <div className="grid grid-cols-2 p-1 bg-white/[0.02] rounded-2xl border border-white/5 shadow-lg">
                  <button
                    type="button"
                    onClick={() => setConversionType('')}
                    disabled={compressing}
                    className={`py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                      conversionType === ''
                        ? 'bg-[#2563EB] text-[#FFFFFF] shadow-[0_0_15px_rgba(37,99,235,0.25)]'
                        : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
                    }`}
                  >
                    Compression Mode
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      // Set default conversion type based on selection
                      if (allImages) setConversionType('image_to_pdf');
                      else if (isSinglePdf) setConversionType('pdf_to_docx');
                      else if (isSingleDocx) setConversionType('docx_to_pdf');
                    }}
                    disabled={compressing}
                    className={`py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                      conversionType !== ''
                        ? 'bg-[#2563EB] text-[#FFFFFF] shadow-[0_0_15px_rgba(37,99,235,0.25)]'
                        : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
                    }`}
                  >
                    Conversion Mode
                  </button>
                </div>
              )}

              {/* Settings Card */}
              <div className="glass rounded-2xl p-6 border border-slate-800/80 space-y-6">
                <h3 className="font-semibold text-slate-300 border-b border-slate-800/60 pb-3 flex items-center gap-2">
                  {conversionType !== '' ? 'Format Conversion Settings' : 'Compression Settings'}
                </h3>

                {/* --------------------- CONVERSION INTERFACE --------------------- */}
                {conversionType !== '' ? (
                  <div className="space-y-4 animate-in fade-in duration-200">
                    
                    {/* Image-to-PDF options */}
                    {allImages && (
                      <div className="space-y-3">
                        <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
                          Image Conversion Format
                        </label>
                        <select
                          value={conversionType}
                          onChange={(e) => setConversionType(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 text-slate-300 rounded-xl py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                        >
                          <option value="image_to_pdf">Merge Images to PDF (.pdf)</option>
                        </select>
                        <p className="text-[10px] text-slate-400 leading-relaxed">
                          All selected images will be combined sequentially into a single multi-page PDF document.
                        </p>
                      </div>
                    )}

                    {/* PDF options */}
                    {isSinglePdf && (
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
                            Target Output Format
                          </label>
                          <select
                            value={conversionType}
                            onChange={(e) => setConversionType(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 text-slate-300 rounded-xl py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="pdf_to_docx">Convert PDF to Word (.docx)</option>
                            <option value="pdf_to_image">Extract Pages as Images</option>
                          </select>
                        </div>

                        {conversionType === 'pdf_to_image' && (
                          <div className="space-y-2 animate-in slide-in-from-top-1 duration-150">
                            <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                              Output Image Format
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                              <button
                                type="button"
                                onClick={() => setTargetImgFormat('PNG')}
                                className={`py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                                  targetImgFormat === 'PNG'
                                    ? 'bg-indigo-500/10 border-indigo-500 text-indigo-400'
                                    : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700'
                                }`}
                              >
                                PNG Images
                              </button>
                              <button
                                type="button"
                                onClick={() => setTargetImgFormat('JPEG')}
                                className={`py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                                  targetImgFormat === 'JPEG'
                                    ? 'bg-indigo-500/10 border-indigo-500 text-indigo-400'
                                    : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700'
                                }`}
                              >
                                JPEG Images
                              </button>
                            </div>
                            <p className="text-[10px] text-slate-400">
                              Pages will be returned inside a single ZIP archive.
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Word-to-PDF options */}
                    {isSingleDocx && (
                      <div className="space-y-3">
                        <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
                          Word Conversion Format
                        </label>
                        <select
                          value={conversionType}
                          onChange={(e) => setConversionType(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 text-slate-300 rounded-xl py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                        >
                          <option value="docx_to_pdf">Convert Word Document to PDF (.pdf)</option>
                        </select>
                        <p className="text-[10px] text-slate-400 leading-relaxed">
                          Converts the .docx file structure natively into a clean letter-sized PDF.
                        </p>
                      </div>
                    )}

                  </div>
                ) : (
                  /* --------------------- COMPRESSION INTERFACE --------------------- */
                  <div className="space-y-6 animate-in fade-in duration-200">
                    
                    {/* Format Conversion Dropdown (Images only) */}
                    {hasImages && (
                      <div className="space-y-2">
                        <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
                          Convert Image Format
                        </label>
                        <select
                          value={targetFormat}
                          onChange={(e) => setTargetFormat(e.target.value)}
                          disabled={compressing}
                          className="w-full bg-slate-900 border border-slate-800 text-slate-300 rounded-xl py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                        >
                          <option value="">Keep Original Format</option>
                          <option value="JPEG">Convert to JPEG (.jpg)</option>
                          <option value="PNG">Convert to PNG (.png)</option>
                          <option value="WEBP">Convert to WebP (.webp)</option>
                        </select>
                      </div>
                    )}

                    {/* Quality Slider (Images only, only if target size optimization is off) */}
                    {hasImages && !optimizeSize && (
                      <div className="space-y-3 animate-in fade-in duration-200">
                        <div className="flex justify-between items-center">
                          <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                            Image Quality
                          </label>
                          <span className="text-sm font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-md border border-indigo-500/20">
                            {quality}%
                          </span>
                        </div>
                        <input 
                          type="range" 
                          min="1" 
                          max="100" 
                          value={quality}
                          onChange={(e) => setQuality(e.target.value)}
                          disabled={compressing}
                          className="w-full accent-indigo-500 cursor-pointer disabled:opacity-50"
                        />
                      </div>
                    )}

                    {/* Target Size Range Optimization */}
                    <div className="space-y-4 pt-4 border-t border-slate-800/60">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                          Target Size Optimization
                        </label>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input 
                            type="checkbox" 
                            checked={optimizeSize}
                            onChange={(e) => setOptimizeSize(e.target.checked)}
                            disabled={compressing}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-500 peer-checked:after:bg-white"></div>
                        </label>
                      </div>

                      {optimizeSize && (
                        <div className="space-y-4 bg-slate-900/40 p-4 border border-slate-800/60 rounded-2xl animate-in slide-in-from-top-2 duration-200">
                          <div className="space-y-2">
                            <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                              Select Target size range
                            </label>
                            <select
                              value={sizePreset}
                              onChange={(e) => setSizePreset(e.target.value)}
                              disabled={compressing}
                              className="w-full bg-slate-950 border border-slate-800 text-slate-300 rounded-xl py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
                            >
                              <option value="under_500kb">Under 500 KB</option>
                              <option value="under_1mb">Under 1 MB (Recommended)</option>
                              <option value="1mb_2mb">1 MB - 2 MB</option>
                              <option value="2mb_5mb">2 MB - 5 MB</option>
                              <option value="custom">Custom Target Range...</option>
                            </select>
                          </div>

                          {sizePreset === 'custom' && (
                            <div className="space-y-3 animate-in slide-in-from-top-1 duration-150">
                              <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                  <span className="text-[10px] text-slate-400 font-medium">Min Target Size</span>
                                  <div className="flex bg-slate-950 border border-slate-800 rounded-xl overflow-hidden focus-within:border-indigo-500">
                                    <input
                                      type="number"
                                      min="0"
                                      value={customMin}
                                      onChange={(e) => setCustomMin(Math.max(0, parseFloat(e.target.value) || 0))}
                                      disabled={compressing}
                                      className="w-full bg-transparent px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
                                    />
                                    <select
                                      value={customMinUnit}
                                      onChange={(e) => setCustomMinUnit(e.target.value)}
                                      disabled={compressing}
                                      className="bg-slate-900 border-l border-slate-800 text-[10px] px-1 text-slate-400 focus:outline-none cursor-pointer"
                                    >
                                      <option value="KB">KB</option>
                                      <option value="MB">MB</option>
                                    </select>
                                  </div>
                                </div>
                                
                                <div className="space-y-1">
                                  <span className="text-[10px] text-slate-400 font-medium">Max Target Size</span>
                                  <div className="flex bg-slate-950 border border-slate-800 rounded-xl overflow-hidden focus-within:border-indigo-500">
                                    <input
                                      type="number"
                                      min="0.01"
                                      step="0.01"
                                      value={customMax}
                                      onChange={(e) => setCustomMax(Math.max(0.01, parseFloat(e.target.value) || 0.01))}
                                      disabled={compressing}
                                      className="w-full bg-transparent px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
                                    />
                                    <select
                                      value={customMaxUnit}
                                      onChange={(e) => setCustomMaxUnit(e.target.value)}
                                      disabled={compressing}
                                      className="bg-slate-900 border-l border-slate-800 text-[10px] px-1 text-slate-400 focus:outline-none cursor-pointer"
                                    >
                                      <option value="KB">KB</option>
                                      <option value="MB">MB</option>
                                    </select>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Archive format (For Bulk Compression) */}
                    <div className="space-y-3 pt-4 border-t border-slate-800/60">
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                        Archive Packaging Format
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          type="button"
                          onClick={() => setArchiveFormat('zip')}
                          disabled={compressing}
                          className={`py-2 px-4 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                            archiveFormat === 'zip'
                              ? 'bg-indigo-500/10 border-indigo-500 text-indigo-400'
                              : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700'
                          }`}
                        >
                          .ZIP Archive
                        </button>
                        <button
                          type="button"
                          onClick={() => setArchiveFormat('tar.gz')}
                          disabled={compressing}
                          className={`py-2 px-4 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                            archiveFormat === 'tar.gz'
                              ? 'bg-indigo-500/10 border-indigo-500 text-indigo-400'
                              : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700'
                          }`}
                        >
                          .TAR.GZ Archive
                        </button>
                      </div>
                    </div>

                  </div>
                )}

                {/* Primary Action Button */}
                <button
                  onClick={handleAction}
                  disabled={files.length === 0 || compressing}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#2563EB] to-[#00F2FE] hover:shadow-[0_0_20px_rgba(0,242,254,0.35)] text-white font-bold text-sm shadow-lg shadow-[#2563EB]/15 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2 group cursor-pointer"
                >
                  {compressing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing file(s)...
                    </>
                  ) : conversionType !== '' ? (
                    <>
                      <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
                      Convert Format
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
                      Compress & Shrink
                    </>
                  )}
                </button>
              </div>

              {/* Error Message banner */}
              {error && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-start gap-3 text-rose-400 text-xs">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="font-bold">Error compiling request:</span>
                    <p className="mt-0.5 leading-relaxed">{error}</p>
                  </div>
                </div>
              )}

              {/* Compression / Conversion Output Result Card */}
              {compressedResult && (
                <div className="glass rounded-2xl p-6 relative overflow-hidden animate-in fade-in slide-in-from-bottom-3 duration-300">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-[#00F2FE]/5 rounded-full blur-2xl pointer-events-none" />

                  <h4 className="text-sm font-bold text-[#00F2FE] drop-shadow-[0_0_8px_rgba(0,242,254,0.3)] uppercase tracking-wider mb-4 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4" /> Ready for Download
                  </h4>

                  <div className="space-y-4">
                    <div className="flex items-start gap-3 bg-white/[0.02] border border-white/5 p-3 rounded-xl">
                      <FileText className="w-8 h-8 text-[#00F2FE] flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-bold text-[#FFFFFF] truncate" title={compressedResult.filename}>
                          {compressedResult.filename}
                        </p>
                        <div className="flex gap-2 text-[10px] text-[#9CA3AF] mt-1">
                          <span>Resulting Size: {formatSize(compressedResult.size)}</span>
                          {conversionType === '' && totalOriginalSize > 0 && (
                            <>
                              <span>•</span>
                              <span className="text-[#10B981] font-extrabold">
                                {Math.round((1 - (compressedResult.size / totalOriginalSize)) * 100)}% smaller
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={handleDownload}
                      className="w-full py-3 px-4 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 group cursor-pointer"
                    >
                      <Download className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" />
                      Download File
                    </button>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}

      </main>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md glass rounded-3xl border border-slate-800/80 p-6 shadow-2xl relative overflow-hidden animate-in zoom-in-95 duration-200 animate-out fade-out">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
            
            <h3 className="text-lg font-bold text-slate-100 mb-2 flex items-center gap-2">
              <Settings className="w-5 h-5 text-indigo-400" />
              API Settings
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Configure the remote FastAPI server URL for compression and format conversion endpoints.
            </p>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Backend API Base URL
                </label>
                <input
                  type="text"
                  placeholder="https://your-backend-api.onrender.com"
                  value={backendUrl}
                  onChange={(e) => setBackendUrl(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl py-2.5 px-4 text-xs focus:outline-none focus:border-indigo-500 text-slate-200 transition-colors"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    localStorage.setItem('backend_api_url', backendUrl);
                    setShowSettings(false);
                  }}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white font-semibold text-xs transition-all cursor-pointer text-center"
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setBackendUrl('https://compressor-and-convertor.onrender.com');
                    localStorage.removeItem('backend_api_url');
                    setShowSettings(false);
                  }}
                  className="py-2.5 px-4 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-semibold text-xs transition-all cursor-pointer text-center"
                >
                  Reset Default
                </button>
                <button
                  type="button"
                  onClick={() => setShowSettings(false)}
                  className="py-2.5 px-4 rounded-xl bg-slate-900/40 border border-transparent hover:border-slate-800 text-slate-400 font-semibold text-xs transition-all cursor-pointer text-center"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <p>© 2026 ShrinkIO. Universal File & Image Compressor. Built with FastAPI and React.</p>
      </footer>
    </div>
  );
}
