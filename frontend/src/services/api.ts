/**
 * バックエンドAPI通信サービス
 */
import axios from 'axios';
import type { RouteRequest, RouteResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒
});

export const api = {
  /**
   * 経路を計算する
   */
  async calculateRoute(request: RouteRequest): Promise<RouteResponse> {
    const response = await apiClient.post<RouteResponse>('/api/v1/routes', request);
    return response.data;
  },

  /**
   * ヘルスチェック
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await apiClient.get('/api/v1/health');
    return response.data;
  },
};
