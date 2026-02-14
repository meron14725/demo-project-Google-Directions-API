/**
 * Google Maps表示コンテナ
 */
import { Map } from '@vis.gl/react-google-maps';
import { RouteDisplay } from './RouteDisplay';
import type { RouteInfo } from '../../types';

interface MapContainerProps {
  route: RouteInfo | null;
  alternativeRoutes?: RouteInfo[];
}

export function MapContainer({ route, alternativeRoutes = [] }: MapContainerProps) {
  // デフォルトの中心位置（東京駅）
  const defaultCenter = { lat: 35.6812, lng: 139.7671 };
  const defaultZoom = 12;
  const mapId = import.meta.env.VITE_MAP_ID;

  console.log('MapContainer - mapId:', mapId);
  console.log('MapContainer - route:', route);

  return (
    <div className="w-full h-[400px] rounded-lg overflow-hidden shadow-md" style={{ height: '400px', width: '100%' }}>
      <Map
        defaultCenter={defaultCenter}
        defaultZoom={defaultZoom}
        gestureHandling="greedy"
        disableDefaultUI={false}
        mapId={mapId}
      >
        {route && (
          <RouteDisplay
            route={route}
            alternativeRoutes={alternativeRoutes}
          />
        )}
      </Map>
    </div>
  );
}
