import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RouteSearchForm } from './RouteSearchForm'

describe('RouteSearchForm', () => {
  const mockOnSearch = vi.fn()

  it('フォームの基本要素が表示される', () => {
    render(<RouteSearchForm onSearch={mockOnSearch} isLoading={false} />)

    expect(screen.getByText('経路検索')).toBeInTheDocument()
    expect(screen.getByLabelText(/出発地/)).toBeInTheDocument()
    expect(screen.getByLabelText(/目的地/)).toBeInTheDocument()
    expect(screen.getByLabelText('移動手段')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '経路を検索' })).toBeInTheDocument()
  })

  it('出発地・目的地を入力して検索できる', async () => {
    const user = userEvent.setup()
    render(<RouteSearchForm onSearch={mockOnSearch} isLoading={false} />)

    await user.type(screen.getByLabelText(/出発地/), '東京駅')
    await user.type(screen.getByLabelText(/目的地/), '渋谷駅')
    await user.click(screen.getByRole('button', { name: '経路を検索' }))

    expect(mockOnSearch).toHaveBeenCalledWith(
      expect.objectContaining({
        origin: '東京駅',
        destination: '渋谷駅',
        travel_mode: 'DRIVE',
      })
    )
  })

  it('ローディング中はボタンが無効化される', () => {
    render(<RouteSearchForm onSearch={mockOnSearch} isLoading={true} />)

    const button = screen.getByRole('button', { name: '検索中...' })
    expect(button).toBeDisabled()
  })

  it('TRANSIT 選択時に出発時刻フィールドが表示される', async () => {
    const user = userEvent.setup()
    render(<RouteSearchForm onSearch={mockOnSearch} isLoading={false} />)

    await user.selectOptions(screen.getByLabelText('移動手段'), 'TRANSIT')

    expect(screen.getByLabelText(/出発時刻/)).toBeInTheDocument()
    expect(screen.getByLabelText('ルーティング設定')).toBeInTheDocument()
    expect(screen.getByText('交通手段フィルタ')).toBeInTheDocument()
  })

  it('TRANSIT 以外では出発時刻フィールドが非表示', () => {
    render(<RouteSearchForm onSearch={mockOnSearch} isLoading={false} />)

    expect(screen.queryByLabelText(/出発時刻/)).not.toBeInTheDocument()
    expect(screen.queryByText('交通手段フィルタ')).not.toBeInTheDocument()
  })

  it('交通手段フィルタのトグルが動作する', async () => {
    const user = userEvent.setup()
    render(<RouteSearchForm onSearch={mockOnSearch} isLoading={false} />)

    await user.selectOptions(screen.getByLabelText('移動手段'), 'TRANSIT')

    const busButton = screen.getByRole('button', { name: 'バス' })
    await user.click(busButton)

    // バスボタンが選択状態のスタイルを持つ
    expect(busButton.className).toContain('bg-blue-600')

    // もう一度クリックで解除
    await user.click(busButton)
    expect(busButton.className).not.toContain('bg-blue-600')
  })
})
