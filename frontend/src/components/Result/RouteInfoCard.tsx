/**
 * ルート情報表示カード
 */
import type { RouteResponse, TransitStep } from '../../types';

interface RouteInfoCardProps {
  routeData: RouteResponse;
}

const getVehicleLabel = (type?: string) => {
  const labels: Record<string, string> = {
    BUS: 'バス',
    SUBWAY: '地下鉄',
    TRAIN: '電車',
    LIGHT_RAIL: 'ライトレール',
    RAIL: '鉄道',
    HEAVY_RAIL: '鉄道',
    COMMUTER_TRAIN: '通勤電車',
    HIGH_SPEED_TRAIN: '新幹線',
    INTERCITY_BUS: '高速バス',
    TROLLEYBUS: 'トロリーバス',
    TRAM: '路面電車',
    FERRY: 'フェリー',
  };
  return type ? labels[type] || type : '';
};

function TransitStepItem({ step }: { step: TransitStep }) {
  if (step.travel_mode === 'WALK') {
    return (
      <div className="flex items-center gap-3 py-2 px-3 bg-gray-50 rounded">
        <span className="text-lg">🚶</span>
        <div className="flex-1">
          <span className="text-sm text-gray-600">徒歩</span>
          {step.duration_text && (
            <span className="text-sm text-gray-500 ml-2">{step.duration_text}</span>
          )}
          {step.distance_text && (
            <span className="text-sm text-gray-500 ml-1">({step.distance_text})</span>
          )}
        </div>
      </div>
    );
  }

  const td = step.transit_details;
  if (!td) return null;

  return (
    <div className="py-3 px-3 bg-blue-50 rounded border border-blue-100">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">🚆</span>
        <span className="font-semibold text-blue-800">
          {td.line_name || td.short_name || ''}
        </span>
        {td.vehicle_type && (
          <span className="text-xs bg-blue-200 text-blue-800 px-2 py-0.5 rounded-full">
            {getVehicleLabel(td.vehicle_type)}
          </span>
        )}
      </div>
      <div className="ml-7 space-y-1 text-sm">
        {td.departure_stop && (
          <div className="text-gray-700">
            <span className="font-medium">{td.departure_stop.name}</span>
            {td.departure_time && (
              <span className="text-gray-500 ml-2">
                {new Date(td.departure_time).toLocaleTimeString('ja-JP', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            )}
          </div>
        )}
        {td.arrival_stop && (
          <div className="text-gray-700">
            <span className="font-medium">{td.arrival_stop.name}</span>
            {td.arrival_time && (
              <span className="text-gray-500 ml-2">
                {new Date(td.arrival_time).toLocaleTimeString('ja-JP', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            )}
          </div>
        )}
        {td.num_stops != null && (
          <span className="text-gray-500">{td.num_stops}駅</span>
        )}
      </div>
    </div>
  );
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

          {route.fare && (
            <div className="flex justify-between items-center py-2 border-b border-gray-200">
              <span className="text-gray-600">運賃</span>
              <span className="font-semibold text-green-700">
                {route.fare.currency_code === 'JPY' ? '¥' : route.fare.currency_code}
                {route.fare.units}
              </span>
            </div>
          )}

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

      {route.transit_steps && route.transit_steps.length > 0 && (
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-bold text-gray-800 mb-3">乗り換え案内</h3>
          <div className="space-y-2">
            {route.transit_steps.map((step, index) => (
              <TransitStepItem key={index} step={step} />
            ))}
          </div>
        </div>
      )}

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
