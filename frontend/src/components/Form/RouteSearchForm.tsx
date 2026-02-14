/**
 * 経路検索フォームコンポーネント
 */
import { useState, FormEvent } from 'react';

interface RouteSearchFormProps {
  onSearch: (data: {
    origin: string;
    destination: string;
    travel_mode: string;
    desired_arrival_time?: string;
  }) => void;
  isLoading: boolean;
}

export function RouteSearchForm({ onSearch, isLoading }: RouteSearchFormProps) {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [travelMode, setTravelMode] = useState('DRIVE');
  const [arrivalTime, setArrivalTime] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    if (!origin.trim() || !destination.trim()) {
      alert('出発地と目的地を入力してください');
      return;
    }

    onSearch({
      origin: origin.trim(),
      destination: destination.trim(),
      travel_mode: travelMode,
      desired_arrival_time: arrivalTime || undefined,
    });
  };

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
