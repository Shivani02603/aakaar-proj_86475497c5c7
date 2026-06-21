```tsx
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface StatCardProps {
  title: string;
  count: number;
  link: string;
}

interface RecentItem {
  id: string;
  name: string;
  createdAt: string;
}

const StatCard = ({ title, count, link }: StatCardProps) => (
  <div className="bg-white shadow-md rounded-lg p-6 flex flex-col items-center">
    <h3 className="text-lg font-semibold text-gray-700">{title}</h3>
    <p className="text-2xl font-bold text-blue-600">{count}</p>
    <Link href={link}>
      <a className="mt-4 text-blue-500 hover:underline">View {title}</a>
    </Link>
  </div>
);

const DashboardPage = () => {
  const [sessionsCount, setSessionsCount] = useState<number>(0);
  const [aiCount, setAiCount] = useState<number>(0);
  const [recentItems, setRecentItems] = useState<RecentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      setError(null);

      try {
        const sessionsResponse = await fetch('/api/sessions');
        const sessionsData = await sessionsResponse.json();
        setSessionsCount(sessionsData.length);

        const aiResponse = await fetch('/api/ai/query');
        const aiData = await aiResponse.json();
        setAiCount(aiData.length);

        const recentResponse = await fetch('/api/sessions');
        const recentData = await recentResponse.json();
        setRecentItems(recentData.slice(0, 5)); // Fetch the first 5 recent items
      } catch (err) {
        setError('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Dashboard</h1>

      {error && (
        <div className="bg-red-100 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center text-gray-500">Loading...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <StatCard title="Sessions" count={sessionsCount} link="/sessions" />
            <StatCard title="AI Queries" count={aiCount} link="/ai" />
          </div>

          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">
              Recent Items
            </h2>
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 px-4 py-2 text-left text-gray-600">
                    Name
                  </th>
                  <th className="border border-gray-300 px-4 py-2 text-left text-gray-600">
                    Created At
                  </th>
                  <th className="border border-gray-300 px-4 py-2 text-left text-gray-600">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentItems.map((item) => (
                  <tr key={item.id}>
                    <td className="border border-gray-300 px-4 py-2 text-gray-700">
                      {item.name}
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-gray-700">
                      {new Date(item.createdAt).toLocaleDateString()}
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-blue-500">
                      <Link href={`/sessions/${item.id}`}>
                        <a className="hover:underline">View</a>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default DashboardPage;
```