'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '@/libs/supabase';
import { Session, User } from '@supabase/supabase-js';


type AuthContextType = {
  session: Session | null;
  user: User | null;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextType>({
  session: null,
  user: null,
  signOut: () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [session, setSession] = useState<Session | null>(null);
  const user = session?.user ?? null;

  useEffect(() => {
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    supabase.auth.getSession().then(({ data }) => setSession(data.session));

    return () => {
      listener?.subscription.unsubscribe();
    };
  }, []);

  const signOut = () => supabase.auth.signOut();

  return (
    <AuthContext.Provider value={{ session, user, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);