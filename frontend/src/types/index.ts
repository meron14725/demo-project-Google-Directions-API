/**
 * TypeScript型定義
 */

export interface RouteRequest {
  origin: string;
  destination: string;
  travel_mode?: string;
  compute_alternative_routes?: boolean;
  desired_arrival_time?: string;
}

export interface RouteInfo {
  duration_seconds: number;
  duration_text: string;
  distance_meters: number;
  distance_text: string;
  polyline?: string;
  start_location: {
    lat: number;
    lng: number;
  };
  end_location: {
    lat: number;
    lng: number;
  };
}

export interface RouteResponse {
  success: boolean;
  route: RouteInfo | null;
  alternative_routes: RouteInfo[];
  recommended_departure_time: string | null;
  travel_mode: string;
  error_message: string | null;
}
