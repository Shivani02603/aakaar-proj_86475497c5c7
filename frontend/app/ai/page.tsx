'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/auth';
import { toast } from 'react-toastify';

interface AiItem {
  id: string;
  query: string;
  answer: string;
  citations: string[];
  createdAt: string;
}

export default function AiListPage() {
  const [aiItems, setAiItems] = useState<AiItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchAiItems = async () => {
      setLoading(true);
      setError(null);

      try {
        const token = getToken();
        const response = await fetch('/api/ai/query', {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch AI items.');
        }

        const data: AiItem[] = await response.json();
        setAiItems(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred.');
      } finally {
        setLoading(false);
      }
    };

    fetchAiItems();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      const token = getToken();
      const response = await fetch(`/api/ai/query/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete AI item.');
      }

      toast.success('AI item deleted successfully.');
      setAiItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'An unknown error occurred.');
    }
  };

  if (loading) {
    return <div className="text-center py-4">Loading...</div>;
  }

  if (error) {
    return <div className="text-center py-4 text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">AI Queries</h1>
      <table className="table-auto w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border border-gray-300 px-4 py-2">ID</th>
            <th className="border border-gray-300 px-4 py-2">Query</th>
            <th className="border border-gray-300 px-4 py-2">Answer</th>
            <th className="border border-gray-300 px-4 py-2">Citations</th>
            <th className="border border-gray-300 px-4 py-2">Created At</th>
            <th className="border border-gray-300 px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {aiItems.map((item) => (
            <tr key={item.id}>
              <td className="border border-gray-300 px-4 py-2">{item.id}</td>
              <td className="border border-gray-300 px-4 py-2">{item.query}</td>
              <td className="border border-gray-300 px-4 py-2">{item.answer}</td>
              <td className="border border-gray-300 px-4 py-2">{item.citations.join(', ')}</td>
              <td className="border border-gray-300 px-4 py-2">{new Date(item.createdAt).toLocaleString()}</td>
              <td className="border border-gray-300 px-4 py-2">
                <button
                  className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                  onClick={() => handleDelete(item.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}