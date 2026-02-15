import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from './api'
import axios from 'axios'
import { mockDriveResponse } from '../test/mocks'

vi.mock('axios', () => {
  const mockInstance = {
    post: vi.fn(),
    get: vi.fn(),
  }
  return {
    default: {
      create: vi.fn(() => mockInstance),
      __mockInstance: mockInstance,
    },
  }
})

function getMockClient() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (axios as unknown as Record<string, any>).__mockInstance
}

describe('api service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('calculateRoute', () => {
    it('POST /api/v1/routes を呼び出してレスポンスを返す', async () => {
      getMockClient().post.mockResolvedValue({ data: mockDriveResponse })

      const result = await api.calculateRoute({
        origin: '東京駅',
        destination: '渋谷駅',
        travel_mode: 'DRIVE',
      })

      expect(getMockClient().post).toHaveBeenCalledWith('/api/v1/routes', {
        origin: '東京駅',
        destination: '渋谷駅',
        travel_mode: 'DRIVE',
      })
      expect(result.success).toBe(true)
      expect(result.route?.duration_text).toBe('25分')
    })

    it('API エラー時に例外がスローされる', async () => {
      getMockClient().post.mockRejectedValue(new Error('Network Error'))

      await expect(
        api.calculateRoute({ origin: '東京駅', destination: '渋谷駅' })
      ).rejects.toThrow('Network Error')
    })
  })

  describe('healthCheck', () => {
    it('GET /api/v1/health を呼び出す', async () => {
      getMockClient().get.mockResolvedValue({
        data: { status: 'ok' },
      })

      const result = await api.healthCheck()
      expect(result.status).toBe('ok')
      expect(getMockClient().get).toHaveBeenCalledWith('/api/v1/health')
    })
  })
})
