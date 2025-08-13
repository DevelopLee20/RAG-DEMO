import React, { useState } from 'react';

const Chat = ({ selectedFile }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
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
    setResponse('');
    setError('');

    try {
      const url = `http://127.0.0.1:8000/stream?name=${encodeURIComponent(selectedFile)}&query=${encodeURIComponent(query)}`;
      const eventSource = new EventSource(url);

      // 서버에서 data 이벤트가 올 때마다 실행
      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close();
          setIsLoading(false);
        } else {
          // 토큰 누적
          setResponse((prev) => prev + event.data);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE Error:', err);
        setError('Stream connection error.');
        eventSource.close();
        setIsLoading(false);
      };
    } catch (err) {
      setError(`Error: ${err.message}`);
      setIsLoading(false);
    }
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
          {isLoading ? 'Streaming...' : 'Execute'}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {response && (
        <div className="mt-4 p-4 bg-gray-100 rounded-lg">
          <h4 className="font-semibold">Response:</h4>
          <p className="text-gray-800 whitespace-pre-wrap">{response}</p>
        </div>
      )}
    </div>
  );
};

export default Chat;
