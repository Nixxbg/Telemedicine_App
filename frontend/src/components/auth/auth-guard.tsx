"use client";

import { useEffect, useState } from "react";
import { PatientProfile, DoctorProfile } from "@/types";

interface AuthGuardProps {
  children: React.ReactNode;
  requiredUserType?: 'patient' | 'doctor';
  fallback?: React.ReactNode;
  onUnauthorized?: () => void;
}

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: PatientProfile | DoctorProfile | null;
  userType: 'patient' | 'doctor' | null;
}

export function AuthGuard({ 
  children, 
  requiredUserType, 
  fallback = <div>Please log in to access this page</div>,
  onUnauthorized 
}: AuthGuardProps) {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    userType: null
  });

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check if we have tokens in localStorage
        const accessToken = localStorage.getItem('access_token');
        const userType = localStorage.getItem('user_type') as 'patient' | 'doctor' | null;
        
        if (!accessToken || !userType) {
          setAuthState({
            isAuthenticated: false,
            isLoading: false,
            user: null,
            userType: null
          });
          return;
        }

        // Verify token with backend
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const userData = await response.json();
          setAuthState({
            isAuthenticated: true,
            isLoading: false,
            user: userData.data,
            userType: userType
          });
        } else {
          // Token is invalid, clear localStorage
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user_type');
          
          setAuthState({
            isAuthenticated: false,
            isLoading: false,
            user: null,
            userType: null
          });
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          user: null,
          userType: null
        });
      }
    };

    checkAuth();
  }, []);

  // Show loading state while checking authentication
  if (authState.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Checking authentication...</span>
      </div>
    );
  }

  // Not authenticated
  if (!authState.isAuthenticated) {
    if (onUnauthorized) {
      onUnauthorized();
    }
    return <>{fallback}</>;
  }

  // User type restriction
  if (requiredUserType && authState.userType !== requiredUserType) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center p-6 max-w-md">
          <h2 className="text-xl font-semibold text-red-600 mb-4">Access Denied</h2>
          <p className="text-gray-600">
            This page is restricted to {requiredUserType}s only.
          </p>
        </div>
      </div>
    );
  }

  // Authenticated and authorized
  return <>{children}</>;
}

// Hook to access auth state in child components
export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    userType: null
  });

  useEffect(() => {
    const checkAuth = () => {
      const accessToken = localStorage.getItem('access_token');
      const userType = localStorage.getItem('user_type') as 'patient' | 'doctor' | null;
      const userDataStr = localStorage.getItem('user_data');
      
      if (accessToken && userType && userDataStr) {
        try {
          const userData = JSON.parse(userDataStr);
          setAuthState({
            isAuthenticated: true,
            isLoading: false,
            user: userData,
            userType: userType
          });
        } catch {
          setAuthState({
            isAuthenticated: false,
            isLoading: false,
            user: null,
            userType: null
          });
        }
      } else {
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          user: null,
          userType: null
        });
      }
    };

    checkAuth();

    // Listen for auth state changes
    const handleStorageChange = () => {
      checkAuth();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('user_data');
    
    setAuthState({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      userType: null
    });
  };

  return {
    ...authState,
    logout
  };
}