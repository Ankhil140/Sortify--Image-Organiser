import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Folder, Image as ImageIcon, Lock, User, LogOut, Loader2, Sparkles } from 'lucide-react';

const API_URL = 'http://localhost:8081';

// --- Login Component --- //
function Login({ onLogin, projectName }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    if (username === 'admin' && password === 'admin') {
      onLogin();
    } else {
      setError('Invalid credentials. Hint: use admin / admin');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 font-sans p-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl"></div>

      <div className="w-full max-w-md p-8 bg-gray-900/80 backdrop-blur-xl rounded-3xl border border-gray-800 shadow-2xl relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="p-4 bg-gray-800/80 rounded-2xl border border-gray-700/50 mb-6 shadow-inner">
            <Sparkles className="w-10 h-10 text-blue-400" />
          </div>
          <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-2">
            {projectName}
          </h2>
          <p className="text-gray-400 text-sm text-center">
            Login to your intelligent asset manager
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-gray-500" />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-gray-950/50 border border-gray-800 rounded-xl text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                placeholder="Username (admin)"
                required
              />
            </div>
          </div>
          
          <div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-500" />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-gray-950/50 border border-gray-800 rounded-xl text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                placeholder="Password (admin)"
                required
              />
            </div>
          </div>

          {error && (
            <div className="text-rose-400 text-sm text-center font-medium bg-rose-500/10 py-2.5 rounded-lg border border-rose-500/20">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25 mt-6 cursor-pointer"
          >
            Access Vault
          </button>
        </form>
      </div>
    </div>
  );
}

// --- Dashboard Component --- //
function Dashboard({ onLogout, projectName }) {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(acceptedFiles);
    setResults(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp']
    }
  });

  const handleUploadAndCluster = async () => {
    if (files.length === 0) return;
    
    setIsProcessing(true);
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_URL}/api/cluster`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (response.data.error) {
        alert(response.data.error);
      } else {
        setResults(response.data.clusters);
      }
    } catch (error) {
      console.error('Clustering failed', error);
      alert('Failed to process images. Ensure the FastAPI backend is running on port 8080.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 font-sans p-8">
      {/* Header */}
      <header className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-10 pb-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-blue-500" />
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
            {projectName}
          </h1>
        </div>
        <button 
          onClick={onLogout} 
          className="flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-gray-300 rounded-xl font-medium transition-colors border border-gray-800 cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </header>

      <div className="max-w-6xl mx-auto space-y-8">
        {/* Upload Zone */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-3xl p-8 shadow-xl">
           <div 
            {...getRootProps()} 
            className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
              isDragActive ? 'border-blue-500 bg-blue-500/5' : 'border-gray-700 hover:border-gray-500 hover:bg-gray-800/50'
            }`}
          >
            <input {...getInputProps()} />
            <UploadCloud className={`w-16 h-16 mx-auto mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-500'}`} />
            <h3 className="text-xl font-medium text-gray-300 mb-2">
              {isDragActive ? 'Drop photos here...' : 'Drag & drop your unstructured photos'}
            </h3>
            <p className="text-gray-500">or click to browse from your computer</p>
            
            {files.length > 0 && (
              <div className="mt-8 p-4 bg-gray-950 rounded-xl inline-block border border-gray-800 shadow-inner">
                <span className="text-blue-400 font-semibold">{files.length} images selected</span>
              </div>
            )}
          </div>

          {files.length > 0 && (
            <div className="mt-8 flex justify-end">
              <button
                onClick={handleUploadAndCluster}
                disabled={isProcessing}
                className="flex items-center gap-2 px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isProcessing ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> AI Analyzing Visually...</>
                ) : (
                  <><Sparkles className="w-5 h-5" /> Semantic Auto-Sort</>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Results View */}
        {results && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <h2 className="text-2xl font-semibold text-gray-100 flex items-center gap-3">
              <Folder className="w-6 h-6 text-purple-400" /> Organized Categories
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(results).map(([category, imageUrls]) => (
                <div key={category} className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-lg transition-transform hover:-translate-y-1">
                  <div className="px-5 py-4 bg-gray-800/50 border-b border-gray-800 flex justify-between items-center">
                    <h3 className="font-medium text-gray-200 capitalize">{category.replace(/_/g, ' ')}</h3>
                    <span className="px-2.5 py-1 bg-gray-950 text-gray-400 text-xs rounded-lg border border-gray-700">
                      {imageUrls.length} items
                    </span>
                  </div>
                  <div className="p-4 grid grid-cols-3 gap-2">
                    {imageUrls.slice(0, 6).map((url, idx) => (
                      <div key={idx} className="aspect-square rounded-lg overflow-hidden bg-gray-950 border border-gray-800">
                        <img src={url} alt={category} className="w-full h-full object-cover" />
                      </div>
                    ))}
                    {imageUrls.length > 6 && (
                      <div className="aspect-square rounded-lg bg-gray-950 border border-gray-800 flex items-center justify-center text-gray-500 text-sm font-medium">
                        +{imageUrls.length - 6}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

// --- App Entry --- //
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const PROJECT_NAME = "Sortify"; // Updated name!

  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} projectName={PROJECT_NAME} />;
  }

  return <Dashboard onLogout={() => setIsAuthenticated(false)} projectName={PROJECT_NAME} />;
}
