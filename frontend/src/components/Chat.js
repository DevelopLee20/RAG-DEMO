import React, { useState } from 'react';

const Chat = ({ selectedFile }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a file to chat with.');
      return;
    }
    if (!query) {
      setError('Please enter a query.');
      return;
    }

    setIsLoading(true);
    setResponse(null);
    setError('');

    try {
      const url = `http://127.0.0.1:8000/chat?name=${encodeURIComponent(selectedFile)}&query=${encodeURIComponent(query)}`;
      const result = await fetch(url);
      const data = await result.json();

      if (result.ok) {
        setResponse(data);
      } else {
        setError(`Error: ${data.detail}`);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    }

    setIsLoading(false);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="chat-query" className="block text-sm font-medium text-gray-700">
            Query
          </label>
          <input 
            id="chat-query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={selectedFile ? `Ask something about ${selectedFile}` : 'Select a file first'}
            disabled={!selectedFile || isLoading}
            className="mt-1 block w-full p-2 border border-gray-300 rounded-lg bg-gray-50 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <button 
          type="submit" 
          disabled={isLoading || !selectedFile}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:bg-gray-400"
        >
          {isLoading ? 'Thinking...' : 'Execute'}
        </button>
      </form>
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      {response && (
        <div className="mt-4 p-4 bg-gray-100 rounded-lg">
          <h4 className="font-semibold">Response:</h4>
          <p className="text-gray-800">{response.detail}</p>
        </div>
      )}
    </div>
  );
};

export default Chat;
