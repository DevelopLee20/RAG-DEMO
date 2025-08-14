import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import FileList from './components/FileList';
import Chat from './components/Chat';
import PdfViewer from './components/PdfViewer';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  const fetchFiles = useCallback(async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/list');
      const data = await response.json();
      if (response.ok) {
        setFiles(data.data || []);
      } else {
        console.error('Failed to fetch files:', data.detail);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleUploadSuccess = () => {
    fetchFiles();
  };

  const handleFileSelect = (file) => {
   if (selectedFile && selectedFile === file) {
      setSelectedFile(null);
    } else {
      setSelectedFile(file);
    }
  };

  return (
    <div className="bg-gray-100 min-h-screen font-sans">
      <Header />
      <main className="container mx-auto p-4" style={{"maxWidth": "100%"}}>
        <div className="flex flex-col md:flex-row gap-8">
          {/* Left Column */}
          <div className="w-full md:w-1/3 flex flex-col gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold mb-4">Upload PDF</h2>
             <FileUpload onUploadSuccess={handleUploadSuccess} />
            </div> 
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold mb-4">Select File</h2>
              <FileList files={files} onFileSelect={handleFileSelect} selectedFile={selectedFile} />
            </div>
          </div>

          {/* Right Column */}
          <div className="w-full md:w-2/3 flex flex-col gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold mb-4">Chat</h2>
              <Chat selectedFile={selectedFile} />
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold mb-4">PDF Viewer</h2>
              <PdfViewer file={selectedFile} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;