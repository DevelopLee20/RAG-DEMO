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

  const handleFileDelete = async (fileName) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/files/${fileName}`, {
        method: 'DELETE',
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // 삭제된 파일이 현재 선택된 파일이면 선택 해제
        if (selectedFile === fileName) {
          setSelectedFile(null);
        }
        // 파일 목록 새로고침
        fetchFiles();
        alert('파일이 성공적으로 삭제되었습니다.');
      } else {
        alert(`파일 삭제 실패: ${data.detail}`);
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      alert('파일 삭제 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="bg-gray-100 min-h-screen font-sans">
      <Header />
      <main className="container mx-auto p-4">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Left Column */}
          <div className="w-full md:w-1/3 flex flex-col gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold mb-4">Upload PDF</h2>
             <FileUpload onUploadSuccess={handleUploadSuccess} />
            </div> 
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold mb-4">Select File</h2>
              <FileList 
                files={files} 
                onFileSelect={handleFileSelect} 
                selectedFile={selectedFile}
                onFileDelete={handleFileDelete}
              />
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