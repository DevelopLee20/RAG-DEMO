import React from 'react';

const FileList = ({ files, onFileSelect, selectedFile }) => {
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
              onClick={() => onFileSelect(file)}
              className={`cursor-pointer p-1 rounded ${selectedFile === file ? 'bg-blue-200' : 'hover:bg-gray-100'}`}
            >
              {file}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default FileList;
