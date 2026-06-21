'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createSession } from '@/lib/api';
import { SessionCreateRequest } from '@/lib/api';

export default function NewSessionPage() {
  const [title, setTitle] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const newSession: SessionCreateRequest = {
      title,
    };

    try {
      await createSession(newSession);
      router.push('/sessions');
    } catch (err) {
      setError('Failed to create session. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Create New Session</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700">
            Title
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-4 py-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
        {error && <div className="text-red-500">{error}</div>}
        <div>
          <button
            type="submit"
            className={`bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Session'}
          </button>
        </div>
      </form>
    </div>
  );
}