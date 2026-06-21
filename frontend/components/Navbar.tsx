'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { isAuthenticated, removeToken } from '@/lib/auth';

export default function Navbar() {
  const [auth, setAuth] = useState(isAuthenticated());
  const router = useRouter();

  const handleLogout = () => {
    removeToken();
    setAuth(false);
    router.push('/login');
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-2 flex justify-between items-center">
        <Link href="/dashboard" className="text-lg font-bold text-blue-600">
          Aakaar Project
        </Link>
        <div className="flex items-center space-x-4">
          {auth ? (
            <>
              <Link href="/sessions" className="text-gray-700 hover:text-blue-600">
                Sessions
              </Link>
              <Link href="/ai" className="text-gray-700 hover:text-blue-600">
                AI
              </Link>
              <button
                onClick={handleLogout}
                className="text-gray-700 hover:text-red-600"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-gray-700 hover:text-blue-600">
                Login
              </Link>
              <Link href="/register" className="text-gray-700 hover:text-blue-600">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}