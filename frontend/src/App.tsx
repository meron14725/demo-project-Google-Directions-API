import { RouteSearchForm } from './components/Form/RouteSearchForm';
import { RouteInfoCard } from './components/Result/RouteInfoCard';
import { MapContainer } from './components/Map/MapContainer';
import { useDirections } from './hooks/useDirections';

function App() {
  const { calculateRoute, isLoading, error, routeData } = useDirections();

  const handleSearch = async (data: {
    origin: string;
    destination: string;
    travel_mode: string;
    desired_arrival_time?: string;
  }) => {
    await calculateRoute({
      origin: data.origin,
      destination: data.destination,
      travel_mode: data.travel_mode,
      desired_arrival_time: data.desired_arrival_time,
    });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto">
        <header className="py-6 px-4 text-center bg-white shadow-sm">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            執事アプリ - 経路検索デモ
          </h1>
          <p className="text-gray-600">
            Google Routes APIを使用した技術検証プロジェクト
          </p>
        </header>

        {/* フォームと結果表示 */}
        <div className="grid md:grid-cols-2 gap-6 p-4">
          <div>
            <RouteSearchForm onSearch={handleSearch} isLoading={isLoading} />
          </div>

          <div>
            {error && (
              <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded mb-4">
                <p className="text-red-700 font-medium">エラー</p>
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {routeData && <RouteInfoCard routeData={routeData} />}

            {!routeData && !error && !isLoading && (
              <div className="p-6 bg-white rounded-lg shadow-md text-center text-gray-500">
                <p>出発地と目的地を入力して、経路を検索してください</p>
              </div>
            )}
          </div>
        </div>

        {/* 地図表示エリア */}
        {routeData && (
          <div className="p-4">
            <MapContainer
              route={routeData.route}
              alternativeRoutes={routeData.alternative_routes || []}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
