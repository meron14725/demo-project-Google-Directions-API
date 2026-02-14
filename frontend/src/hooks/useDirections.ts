/**
 * 経路検索カスタムフック
 */
import { useState } from 'react';
import { api } from '../services/api';
import type { RouteRequest, RouteResponse } from '../types';

export function useDirections() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);

  const calculateRoute = async (request: RouteRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await api.calculateRoute(request);

      if (!data.success) {
        setError(data.error_message || '経路の計算に失敗しました');
        setRouteData(null);
        return null;
      }

      setRouteData(data);
      return data;
    } catch (err) {
      const message = err instanceof Error
        ? err.message
        : '経路検索に失敗しました。もう一度お試しください。';
      setError(message);
      setRouteData(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setRouteData(null);
    setError(null);
    setIsLoading(false);
  };

  return {
    calculateRoute,
    reset,
    isLoading,
    error,
    routeData,
  };
}
