import React from 'react';

const FileList = ({ files, onFileSelect, selectedFile, onFileDelete }) => {
  const handleDelete = (e, file) => {
    e.stopPropagation(); // 클릭 이벤트가 부모로 전파되지 않도록 방지
    if (window.confirm(`"${file}" 파일을 삭제하시겠습니까?`)) {
      onFileDelete(file);
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">Available Files:</h3>
      {files.length === 0 ? (
        <p className="text-sm text-gray-500">No files uploaded yet.</p>
      ) : (
        <ul className="list-disc list-inside">
          {files.map((file) => (
            <li 
              key={file}
              className={`cursor-pointer p-1 rounded flex justify-between items-center ${selectedFile === file ? 'bg-blue-200' : 'hover:bg-gray-100'}`}
            >
              <span 
                onClick={() => onFileSelect(file)}
                className="flex-1"
              >
                {file}
              </span>
              <button
                onClick={(e) => handleDelete(e, file)}
                className="ml-2 px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                title="Delete file"
              >
                삭제
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default FileList;
