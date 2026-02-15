/**
 * ルート描画コンポーネント（マーカー + ポリライン）
 */
import { AdvancedMarker, useMap } from '@vis.gl/react-google-maps';
import { useEffect, useRef } from 'react';
import type { RouteInfo } from '../../types';

interface RouteDisplayProps {
  route: RouteInfo;
  alternativeRoutes?: RouteInfo[];
}

export function RouteDisplay({ route, alternativeRoutes = [] }: RouteDisplayProps) {
  const map = useMap();
  const polylinesRef = useRef<google.maps.Polyline[]>([]);

  // ポリラインをデコードして描画
  useEffect(() => {
    if (!map || !route.polyline) {
      return;
    }

    // 既存のポリラインをクリア
    polylinesRef.current.forEach((polyline) => polyline.setMap(null));

    const newPolylines: google.maps.Polyline[] = [];

    // メインルートのポリライン
    const mainPath = decodePolyline(route.polyline);

    const mainPolyline = new google.maps.Polyline({
      path: mainPath,
      geodesic: true,
      strokeColor: '#2563EB', // blue-600
      strokeOpacity: 1.0,
      strokeWeight: 4,
      map: map,
    });
    newPolylines.push(mainPolyline);

    // 代替ルートのポリライン
    alternativeRoutes.forEach((altRoute) => {
      if (altRoute.polyline) {
        const altPath = decodePolyline(altRoute.polyline);
        const altPolyline = new google.maps.Polyline({
          path: altPath,
          geodesic: true,
          strokeColor: '#9CA3AF', // gray-400
          strokeOpacity: 0.7,
          strokeWeight: 3,
          map: map,
        });
        newPolylines.push(altPolyline);
      }
    });

    // ポリラインを保存（クリーンアップ用）
    polylinesRef.current = newPolylines;

    // ルート全体が見えるようにビューを調整
    const bounds = new google.maps.LatLngBounds();
    bounds.extend(route.start_location);
    bounds.extend(route.end_location);
    map.fitBounds(bounds, { top: 50, right: 50, bottom: 50, left: 50 });

    return () => {
      newPolylines.forEach((polyline) => polyline.setMap(null));
    };
  }, [map, route, alternativeRoutes]);

  return (
    <>
      {/* 出発地マーカー */}
      <AdvancedMarker
        position={route.start_location}
        title="出発地"
      >
        <div className="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold shadow-lg">
          A
        </div>
      </AdvancedMarker>

      {/* 目的地マーカー */}
      <AdvancedMarker
        position={route.end_location}
        title="目的地"
      >
        <div className="bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold shadow-lg">
          B
        </div>
      </AdvancedMarker>
    </>
  );
}

/**
 * Encoded Polylineをデコード
 * Google Maps Polyline Encoding Algorithm
 */
function decodePolyline(encoded: string): google.maps.LatLngLiteral[] {
  const poly: google.maps.LatLngLiteral[] = [];
  let index = 0;
  const len = encoded.length;
  let lat = 0;
  let lng = 0;

  while (index < len) {
    let b: number;
    let shift = 0;
    let result = 0;

    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;

    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    poly.push({ lat: lat / 1e5, lng: lng / 1e5 });
  }

  return poly;
}
