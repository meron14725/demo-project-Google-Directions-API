/**
 * テスト用モックデータ
 */
import type { RouteResponse, RouteInfo, TransitStep } from '../types'

export const mockRouteInfo: RouteInfo = {
  duration_seconds: 1500,
  duration_text: '25分',
  distance_meters: 5200,
  distance_text: '5.2 km',
  polyline: 'abc123',
  start_location: { lat: 35.6812, lng: 139.7671 },
  end_location: { lat: 35.658, lng: 139.7016 },
}

export const mockTransitSteps: TransitStep[] = [
  {
    travel_mode: 'WALK',
    duration_text: '3分',
    distance_text: '200 m',
  },
  {
    travel_mode: 'TRANSIT',
    duration_text: '10分',
    distance_text: '5.0 km',
    transit_details: {
      departure_stop: { name: '東京駅' },
      arrival_stop: { name: '渋谷駅' },
      departure_time: '2026-02-14T14:00:00Z',
      arrival_time: '2026-02-14T14:30:00Z',
      line_name: '山手線',
      short_name: 'JY',
      vehicle_type: 'TRAIN',
      num_stops: 5,
    },
  },
  {
    travel_mode: 'WALK',
    duration_text: '2分',
    distance_text: '150 m',
  },
]

export const mockDriveResponse: RouteResponse = {
  success: true,
  route: mockRouteInfo,
  alternative_routes: [],
  recommended_departure_time: null,
  travel_mode: 'DRIVE',
  error_message: null,
}

export const mockTransitResponse: RouteResponse = {
  success: true,
  route: {
    ...mockRouteInfo,
    transit_steps: mockTransitSteps,
    fare: { currency_code: 'JPY', units: '200' },
  },
  alternative_routes: [],
  recommended_departure_time: null,
  travel_mode: 'TRANSIT',
  error_message: null,
}

export const mockErrorResponse: RouteResponse = {
  success: false,
  route: null,
  alternative_routes: [],
  recommended_departure_time: null,
  travel_mode: 'DRIVE',
  error_message: 'ルートが見つかりませんでした',
}
