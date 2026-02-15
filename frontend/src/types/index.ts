/**
 * TypeScript型定義
 */

export interface TransitPreferences {
  routing_preference?: string;
  allowed_travel_modes?: string[];
}

export interface RouteRequest {
  origin: string;
  destination: string;
  travel_mode?: string;
  compute_alternative_routes?: boolean;
  desired_arrival_time?: string;
  departure_time?: string;
  transit_preferences?: TransitPreferences;
}

export interface TransitStop {
  name: string;
  location?: {
    lat: number;
    lng: number;
  };
}

export interface TransitDetails {
  departure_stop?: TransitStop;
  arrival_stop?: TransitStop;
  departure_time?: string;
  arrival_time?: string;
  line_name?: string;
  short_name?: string;
  vehicle_type?: string;
  num_stops?: number;
}

export interface TransitStep {
  travel_mode: string;
  duration_text?: string;
  distance_text?: string;
  transit_details?: TransitDetails;
}

export interface FareInfo {
  currency_code: string;
  units: string;
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
  transit_steps?: TransitStep[];
  fare?: FareInfo;
}

export interface RouteResponse {
  success: boolean;
  route: RouteInfo | null;
  alternative_routes: RouteInfo[];
  recommended_departure_time: string | null;
  travel_mode: string;
  error_message: string | null;
}
