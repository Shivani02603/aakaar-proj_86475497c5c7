import { ReactNode } from 'react';
import { useAuth } from '@/providers/AuthProvider';
import { redirect } from 'next/navigation';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    redirect('/login');
    return null;
  }

  return <div className="p-4">{children}</div>;
}