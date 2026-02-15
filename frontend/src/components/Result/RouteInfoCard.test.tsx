import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RouteInfoCard } from './RouteInfoCard'
import {
  mockDriveResponse,
  mockTransitResponse,
  mockErrorResponse,
} from '../../test/mocks'

describe('RouteInfoCard', () => {
  it('DRIVE ルート情報を正しく表示する', () => {
    render(<RouteInfoCard routeData={mockDriveResponse} />)

    expect(screen.getByText('ルート情報')).toBeInTheDocument()
    expect(screen.getByText('車')).toBeInTheDocument()
    expect(screen.getByText('25分')).toBeInTheDocument()
    expect(screen.getByText('5.2 km')).toBeInTheDocument()
  })

  it('route が null の場合何も表示しない', () => {
    const { container } = render(<RouteInfoCard routeData={mockErrorResponse} />)
    expect(container.innerHTML).toBe('')
  })

  it('TRANSIT ルートで乗り換え案内が表示される', () => {
    render(<RouteInfoCard routeData={mockTransitResponse} />)

    expect(screen.getByText('乗り換え案内')).toBeInTheDocument()
    expect(screen.getByText('山手線')).toBeInTheDocument()
    expect(screen.getByText('東京駅')).toBeInTheDocument()
    expect(screen.getByText('渋谷駅')).toBeInTheDocument()
    expect(screen.getByText('5駅')).toBeInTheDocument()
  })

  it('TRANSIT ルートで運賃が表示される', () => {
    render(<RouteInfoCard routeData={mockTransitResponse} />)

    expect(screen.getByText('運賃')).toBeInTheDocument()
    expect(screen.getByText('¥200')).toBeInTheDocument()
  })

  it('推奨出発時刻がある場合に表示される', () => {
    const responseWithDeparture = {
      ...mockDriveResponse,
      recommended_departure_time: '2026-02-14T14:35:00',
    }
    render(<RouteInfoCard routeData={responseWithDeparture} />)

    expect(screen.getByText('推奨出発時刻')).toBeInTheDocument()
  })

  it('代替ルートがある場合に表示される', () => {
    const responseWithAlts = {
      ...mockDriveResponse,
      alternative_routes: [
        {
          duration_seconds: 2000,
          duration_text: '33分',
          distance_meters: 7000,
          distance_text: '7.0 km',
          start_location: { lat: 35.6812, lng: 139.7671 },
          end_location: { lat: 35.658, lng: 139.7016 },
        },
      ],
    }
    render(<RouteInfoCard routeData={responseWithAlts} />)

    expect(screen.getByText('代替ルート')).toBeInTheDocument()
    expect(screen.getByText('ルート 2')).toBeInTheDocument()
    expect(screen.getByText('33分')).toBeInTheDocument()
  })
})
