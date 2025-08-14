import React, { useState } from 'react';
import { Document, Page } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

import { GlobalWorkerOptions } from 'pdfjs-dist';

GlobalWorkerOptions.workerSrc = `/pdf.worker.min.mjs`;

const PdfViewer = ({ file }) => {
  const [numPages, setNumPages] = useState(null);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  if (!file) {
    return <div className="text-center text-gray-500">Select a PDF file to view.</div>;
  }

  const fileUrl = `http://127.0.0.1:8000/files/${encodeURIComponent(file)}`;

  return (
    <div className="pdf-viewer-container" style={{ maxHeight: '600px', overflowY: 'auto', border: '1px solid #ccc' }}>
      <Document
        file={fileUrl}
        onLoadSuccess={onDocumentLoadSuccess}
        onLoadError={(error) => console.error('Error while loading PDF:', error)}
      >
        {Array.from(new Array(numPages), (el, index) => (
          <Page key={`page_${index + 1}`} pageNumber={index + 1} width={800} />
        ))}
      </Document>
    </div>
  );
};

export default PdfViewer;
