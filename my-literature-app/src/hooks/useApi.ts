import { useState, useCallback } from 'react';
import { ApiError } from '@/lib/api/types';

// 定义API状态类型
type ApiStatus = 'idle' | 'loading' | 'success' | 'error';

// 自定义Hook
const useApi = <T,>(apiFunction: (...args: any[]) => Promise<T>) => {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [status, setStatus] = useState<ApiStatus>('idle');

  const execute = useCallback(
    async (...args: any[]) => {
      setStatus('loading');
      setError(null);
      
      try {
        const response = await apiFunction(...args);
        setData(response);
        setStatus('success');
        return response;
      } catch (err) {
        setError(err as ApiError);
        setStatus('error');
        throw err;
      }
    },
    [apiFunction]
  );

  return { execute, data, error, status, isLoading: status === 'loading' };
};

export default useApi;