import React, { useState, useRef } from 'react';

const Chat = ({ selectedFile }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState([]); // 이전 메시지까지 누적
  const [error, setError] = useState('');

  // 세션 ID를 한 번 생성해서 유지
  const sessionIdRef = useRef(`sess_${Math.random().toString(36).substr(2, 9)}`);

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
    setError('');

    // 사용자가 보낸 메시지 기록 추가
    setMessages((prev) => [...prev, { role: 'user', content: query }]);

    try {
      const url = `http://127.0.0.1:8000/stream?name=${encodeURIComponent(selectedFile)}&query=${encodeURIComponent(query)}&session_id=${sessionIdRef.current}`;
      const eventSource = new EventSource(url);

      let aiMessage = ''; // 스트리밍 중인 AI 메시지 누적

      eventSource.onmessage = (event) => {
        console.debug('SSE message:', event.data);
        if (event.data === '[DONE]') {
          eventSource.close();
          // 최종 완료 시 로딩 해제만 수행 (실시간으로 이미 메시지를 반영함)
          setIsLoading(false);
          aiMessage = '';
        } else {
          aiMessage += event.data;
          // 실시간으로 마지막 AI 메시지 업데이트 (없으면 새로 추가)
          setMessages((prev) => {
            if (prev.length > 0 && prev[prev.length - 1].role === 'ai') {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: updated[updated.length - 1].content + event.data,
              };
              return updated;
            }
            return [...prev, { role: 'ai', content: event.data }];
          });
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

    setQuery(''); // 입력창 초기화
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

      {messages.length > 0 && (
        <div className="mt-4">
          <h4 className="font-semibold text-gray-800 mb-2">Chat History:</h4>
          <div className="h-96 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50">
            <div className="space-y-4">
              {messages.slice().map((msg, idx) => (
                <div
                  key={messages.length - 1 - idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-800'
                    }`}
                  >
                    <div className="text-xs font-medium mb-1 opacity-75">
                      {msg.role === 'user' ? 'You' : 'AI'}
                    </div>
                    <div className="whitespace-pre-wrap text-sm">
                      {msg.content}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
