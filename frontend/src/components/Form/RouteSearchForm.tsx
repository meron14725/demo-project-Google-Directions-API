/**
 * 経路検索フォームコンポーネント
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import type { TransitPreferences } from '../../types';

interface RouteSearchFormProps {
  onSearch: (data: {
    origin: string;
    destination: string;
    travel_mode: string;
    desired_arrival_time?: string;
    departure_time?: string;
    transit_preferences?: TransitPreferences;
  }) => void;
  isLoading: boolean;
}

export function RouteSearchForm({ onSearch, isLoading }: RouteSearchFormProps) {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [travelMode, setTravelMode] = useState('DRIVE');
  const [arrivalTime, setArrivalTime] = useState('');
  const [departureTime, setDepartureTime] = useState('');
  const [routingPreference, setRoutingPreference] = useState('');
  const [allowedModes, setAllowedModes] = useState<string[]>([]);

  const isTransit = travelMode === 'TRANSIT';

  const handleModeToggle = (mode: string) => {
    setAllowedModes((prev) =>
      prev.includes(mode) ? prev.filter((m) => m !== mode) : [...prev, mode]
    );
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    if (!origin.trim() || !destination.trim()) {
      alert('出発地と目的地を入力してください');
      return;
    }

    const searchData: Parameters<typeof onSearch>[0] = {
      origin: origin.trim(),
      destination: destination.trim(),
      travel_mode: travelMode,
      desired_arrival_time: arrivalTime || undefined,
    };

    if (isTransit) {
      if (departureTime) {
        searchData.departure_time = departureTime;
      }
      const prefs: TransitPreferences = {};
      if (routingPreference) {
        prefs.routing_preference = routingPreference;
      }
      if (allowedModes.length > 0) {
        prefs.allowed_travel_modes = allowedModes;
      }
      if (prefs.routing_preference || prefs.allowed_travel_modes) {
        searchData.transit_preferences = prefs;
      }
    }

    onSearch(searchData);
  };

  const transitModeOptions = [
    { value: 'BUS', label: 'バス' },
    { value: 'SUBWAY', label: '地下鉄' },
    { value: 'TRAIN', label: '電車' },
    { value: 'LIGHT_RAIL', label: 'ライトレール' },
    { value: 'RAIL', label: '鉄道全般' },
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">経路検索</h2>

      <div>
        <label htmlFor="origin" className="block text-sm font-medium text-gray-700 mb-1">
          出発地 *
        </label>
        <input
          id="origin"
          type="text"
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
          placeholder="例: 東京駅"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />
      </div>

      <div>
        <label htmlFor="destination" className="block text-sm font-medium text-gray-700 mb-1">
          目的地 *
        </label>
        <input
          id="destination"
          type="text"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          placeholder="例: 渋谷駅"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />
      </div>

      <div>
        <label htmlFor="travel-mode" className="block text-sm font-medium text-gray-700 mb-1">
          移動手段
        </label>
        <select
          id="travel-mode"
          value={travelMode}
          onChange={(e) => setTravelMode(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        >
          <option value="DRIVE">車</option>
          <option value="WALK">徒歩</option>
          <option value="TRANSIT">公共交通機関</option>
          <option value="BICYCLE">自転車</option>
        </select>
      </div>

      {isTransit && (
        <div>
          <label htmlFor="departure-time" className="block text-sm font-medium text-gray-700 mb-1">
            出発時刻（オプション）
          </label>
          <input
            id="departure-time"
            type="datetime-local"
            value={departureTime}
            onChange={(e) => setDepartureTime(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">未指定の場合は現在時刻で検索します</p>
        </div>
      )}

      <div>
        <label htmlFor="arrival-time" className="block text-sm font-medium text-gray-700 mb-1">
          到着希望時刻（オプション）
        </label>
        <input
          id="arrival-time"
          type="datetime-local"
          value={arrivalTime}
          onChange={(e) => setArrivalTime(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />
      </div>

      {isTransit && (
        <>
          <div>
            <label htmlFor="routing-pref" className="block text-sm font-medium text-gray-700 mb-1">
              ルーティング設定
            </label>
            <select
              id="routing-pref"
              value={routingPreference}
              onChange={(e) => setRoutingPreference(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            >
              <option value="">指定なし</option>
              <option value="LESS_WALKING">徒歩を減らす</option>
              <option value="FEWER_TRANSFERS">乗り換えを減らす</option>
            </select>
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-700 mb-2">
              交通手段フィルタ
            </span>
            <div className="flex flex-wrap gap-2">
              {transitModeOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => handleModeToggle(opt.value)}
                  disabled={isLoading}
                  className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                    allowedModes.includes(opt.value)
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">未選択の場合はすべての交通手段を使用</p>
          </div>
        </>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium transition-colors"
      >
        {isLoading ? '検索中...' : '経路を検索'}
      </button>
    </form>
  );
}
