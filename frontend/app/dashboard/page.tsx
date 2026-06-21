```tsx
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/providers/AuthProvider';
import { getToken } from '@/lib/auth';
import { listSessions, listFiles, aiQuery } from '@/api/client';
import Link from 'next/link';

interface Session {
  id: string;
  name: string;
  createdAt: string;
}

interface File {
  id: string;
  filename: string;
  originalFilename: string;
  fileSize: number;
  createdAt: string;
}

interface AiQueryResponse {
  id: string;
  query: string;
  createdAt: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [aiQueries, setAiQueries] = useState<AiQueryResponse[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const token = getToken();
        if (!token) {
          throw new Error('Authentication token is missing.');
        }

        const [sessionsResponse, filesResponse, aiQueriesResponse] = await Promise.all([
          listSessions(token),
          listFiles(token),
          aiQuery(token),
        ]);

        setSessions(sessionsResponse);
        setFiles(filesResponse);
        setAiQueries(aiQueriesResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-white shadow rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Sessions</h2>
          <p className="text-2xl font-bold">{sessions.length}</p>
          <Link href="/sessions" className="text-blue-500 hover:underline">
            View all sessions
          </Link>
        </div>

        <div className="bg-white shadow rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Files</h2>
          <p className="text-2xl font-bold">{files.length}</p>
          <Link href="/files" className="text-blue-500 hover:underline">
            View all files
          </Link>
        </div>

        <div className="bg-white shadow rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">AI Queries</h2>
          <p className="text-2xl font-bold">{aiQueries.length}</p>
          <Link href="/ai" className="text-blue-500 hover:underline">
            View all AI queries
          </Link>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Items</h2>
        <table className="w-full border-collapse border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-200 p-2 text-left">Type</th>
              <th className="border border-gray-200 p-2 text-left">Name</th>
              <th className="border border-gray-200 p-2 text-left">Created At</th>
            </tr>
          </thead>
          <tbody>
            {sessions.slice(0, 5).map((session) => (
              <tr key={session.id}>
                <td className="border border-gray-200 p-2">Session</td>
                <td className="border border-gray-200 p-2">{session.name}</td>
                <td className="border border-gray-200 p-2">{new Date(session.createdAt).toLocaleString()}</td>
              </tr>
            ))}
            {files.slice(0, 5).map((file) => (
              <tr key={file.id}>
                <td className="border border-gray-200 p-2">File</td>
                <td className="border border-gray-200 p-2">{file.originalFilename}</td>
                <td className="border border-gray-200 p-2">{new Date(file.createdAt).toLocaleString()}</td>
              </tr>
            ))}
            {aiQueries.slice(0, 5).map((query) => (
              <tr key={query.id}>
                <td className="border border-gray-200 p-2">AI Query</td>
                <td className="border border-gray-200 p-2">{query.query}</td>
                <td className="border border-gray-200 p-2">{new Date(query.createdAt).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```