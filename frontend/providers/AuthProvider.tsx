'use client';

import { createContext, useState, useEffect } from 'react';
import { isAuthenticated, getUser } from '@/lib/auth';

interface AuthContextType {
  isAuth: boolean;
  user: Record<string, unknown> | null;
}

export const AuthContext = createContext<AuthContextType>({
  isAuth: false,
  user: null,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuth, setIsAuth] = useState(false);
  const [user, setUser] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const authStatus = isAuthenticated();
    setIsAuth(authStatus);
    if (authStatus) {
      setUser(getUser());
    }
  }, []);

  return (
    <AuthContext.Provider value={{ isAuth, user }}>
      {children}
    </AuthContext.Provider>
  );
}