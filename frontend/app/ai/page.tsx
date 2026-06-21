'use client';

import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { aiQuery } from '@/api/client';
import { useRouter } from 'next/navigation';

interface AiItem {
  id: string;
  query: string;
  response: string;
  createdAt: string;
}

export default function AiListPage() {
  const [aiItems, setAiItems] = useState<AiItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchAiItems = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await aiQuery();
        setAiItems(response.data);
      } catch (err) {
        setError('Failed to fetch AI items.');
        toast.error('Error fetching AI items.');
      } finally {
        setLoading(false);
      }
    };

    fetchAiItems();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      await fetch(`/api/ai/${id}`, { method: 'DELETE' });
      setAiItems((prev) => prev.filter((item) => item.id !== id));
      toast.success('AI item deleted successfully.');
    } catch (err) {
      setError('Failed to delete AI item.');
      toast.error('Error deleting AI item.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center mt-10">Loading...</div>;
  }

  if (error) {
    return <div className="text-center mt-10 text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">AI List</h1>
      <table className="table-auto w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border border-gray-300 px-4 py-2">ID</th>
            <th className="border border-gray-300 px-4 py-2">Query</th>
            <th className="border border-gray-300 px-4 py-2">Response</th>
            <th className="border border-gray-300 px-4 py-2">Created At</th>
            <th className="border border-gray-300 px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {aiItems.map((item) => (
            <tr key={item.id}>
              <td className="border border-gray-300 px-4 py-2">{item.id}</td>
              <td className="border border-gray-300 px-4 py-2">{item.query}</td>
              <td className="border border-gray-300 px-4 py-2">{item.response}</td>
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