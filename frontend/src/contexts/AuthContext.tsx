/* eslint-disable react-refresh/only-export-components */
/**
 * Authentication context for global user state management.
 */
import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { authService, User, AuthError } from '@/services/authService';
import { clearUserToken } from '@/utils/token';
import { clearPlayerData } from '@/utils/player';
import { useToast } from '@/hooks/use-toast';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, nickname: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const initAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (error: unknown) {
        const status = error instanceof AuthError ? error.status : 0;

        // 鍒嗙被澶勭悊閿欒
        if (status === 401 || status === 403) {
          // Token 杩囨湡/鏃犳晥:闈欓粯澶辫触,娓呯悊鐘舵€?鐢ㄦ埛闇€閲嶆柊鐧诲綍
          clearUserToken();
          setUser(null);
        } else if (status >= 500) {
          // 鏈嶅姟鍣ㄩ敊璇?鎻愮ず鐢ㄦ埛
          console.error('Server error during auth:', error);
          toast({
            variant: "destructive",
            title: "鏈嶅姟杩炴帴澶辫触",
            description: "Unable to connect to the server. Please try again later.",
          });
          setUser(null);
        } else {
          // 缃戠粶鏂紑绛夊叾浠栭敊璇?
          console.warn('Network/Auth init error:', error);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [toast]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authService.login(email, password);
    setUser(response.user);
  }, []);

  const register = useCallback(async (email: string, password: string, nickname: string) => {
    const response = await authService.register(email, password, nickname);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local cleanup even if server request fails
    } finally {
      // Always clear local state regardless of server response
      clearPlayerData(); // 娓呴櫎鎵€鏈夋湰鍦版暟鎹紙player_id, nickname, tokens锛?
      clearUserToken();
      setUser(null);
    }
  }, []);

  const updateUser = useCallback((updates: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...updates } : null));
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      throw error;
    }
  }, []);

  const value = useMemo<AuthContextType>(() => ({
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    updateUser,
    refreshUser,
  }), [user, isLoading, login, register, logout, updateUser, refreshUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
