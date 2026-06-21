'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/auth';
import { SessionResponse } from '@/lib/api';

interface Session {
  id: string;
  name: string;
  createdAt: string;
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchSessions = async () => {
      setLoading(true);
      setError(null);

      try {
        const token = getToken();
        const response = await fetch('/api/sessions', {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch sessions');
        }

        const data: SessionResponse[] = await response.json();
        setSessions(data.map((session) => ({
          id: session.id,
          name: session.name,
          createdAt: session.createdAt,
        })));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, []);

  const handleDelete = async (id: string) => {
    setError(null);

    try {
      const token = getToken();
      const response = await fetch(`/api/sessions/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      setSessions((prev) => prev.filter((session) => session.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Sessions</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && sessions.length === 0 && <p>No sessions found.</p>}
      {!loading && sessions.length > 0 && (
        <table className="table-auto w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-300 px-4 py-2">ID</th>
              <th className="border border-gray-300 px-4 py-2">Name</th>
              <th className="border border-gray-300 px-4 py-2">Created At</th>
              <th className="border border-gray-300 px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr key={session.id}>
                <td className="border border-gray-300 px-4 py-2">{session.id}</td>
                <td className="border border-gray-300 px-4 py-2">{session.name}</td>
                <td className="border border-gray-300 px-4 py-2">{new Date(session.createdAt).toLocaleString()}</td>
                <td className="border border-gray-300 px-4 py-2">
                  <button
                    className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                    onClick={() => handleDelete(session.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}