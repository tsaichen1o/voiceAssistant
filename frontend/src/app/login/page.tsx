'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { FaGoogle } from "react-icons/fa";


export default function LoginPage() {
  const router = useRouter();
  const { user, loading, signInWithGoogle } = useAuth();

  useEffect(() => {
    if (user && !loading) {
      router.push('/');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#E7E7E7]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#2F70B3]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#E7E7E7]">
      <div className="w-[88%] max-w-md p-8 space-y-8 bg-[#FAFAFA] rounded-lg shadow-md">
        <div className="text-center">
          <Image
            src="/icons/logo_FFF.png"
            width={80}
            height={80}
            alt="go42TUM Logo"
            className="mx-auto"
          />
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Welcome to go42TUM
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Please sign in to continue
          </p>
        </div>

        <div className="mt-8">
          <button
            onClick={signInWithGoogle}
            className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-[#2F70B3] hover:bg-[#2460A0] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2F70B3]"
          >
            <FaGoogle className="size-5 mr-2" />
            Sign in with Google
          </button>
        </div>
      </div>
    </div>
  );
}