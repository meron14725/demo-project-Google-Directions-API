/**
 * ルート情報表示カード
 */
import type { RouteResponse } from '../../types';

interface RouteInfoCardProps {
  routeData: RouteResponse;
}

export function RouteInfoCard({ routeData }: RouteInfoCardProps) {
  if (!routeData.route) {
    return null;
  }

  const { route, recommended_departure_time, travel_mode } = routeData;

  const getTravelModeLabel = (mode: string) => {
    const labels: Record<string, string> = {
      DRIVE: '車',
      WALK: '徒歩',
      TRANSIT: '公共交通機関',
      BICYCLE: '自転車',
    };
    return labels[mode] || mode;
  };

  const formatDateTime = (isoString: string | null) => {
    if (!isoString) return null;

    const date = new Date(isoString);
    return new Intl.DateTimeFormat('ja-JP', {
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <div className="space-y-4">
      <div className="p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">ルート情報</h2>

        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-200">
            <span className="text-gray-600">移動手段</span>
            <span className="font-semibold text-gray-800">{getTravelModeLabel(travel_mode)}</span>
          </div>

          <div className="flex justify-between items-center py-2 border-b border-gray-200">
            <span className="text-gray-600">所要時間</span>
            <span className="font-semibold text-blue-600 text-lg">{route.duration_text}</span>
          </div>

          <div className="flex justify-between items-center py-2 border-b border-gray-200">
            <span className="text-gray-600">距離</span>
            <span className="font-semibold text-gray-800">{route.distance_text}</span>
          </div>

          {recommended_departure_time && (
            <div className="mt-4 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
              <p className="text-sm text-gray-600 mb-1">推奨出発時刻</p>
              <p className="text-xl font-bold text-blue-700">
                {formatDateTime(recommended_departure_time)}
              </p>
              <p className="text-sm text-gray-600 mt-2">
                この時刻に出発すれば、到着希望時刻に間に合います
              </p>
            </div>
          )}
        </div>
      </div>

      {routeData.alternative_routes.length > 0 && (
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-bold text-gray-800 mb-3">代替ルート</h3>
          <div className="space-y-2">
            {routeData.alternative_routes.map((altRoute, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded border border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">ルート {index + 2}</span>
                  <div className="text-right">
                    <span className="font-semibold text-gray-800 mr-3">
                      {altRoute.duration_text}
                    </span>
                    <span className="text-gray-600 text-sm">{altRoute.distance_text}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
