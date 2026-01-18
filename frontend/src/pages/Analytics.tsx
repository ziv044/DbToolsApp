import { useState } from 'react'
import { useAnalyticsData } from '../hooks/useAnalyticsData'
import { DateRangePicker, ServerSelector, QueryDetailModal } from '../components/analytics'
import {
  PiePanel,
  BarPanel,
  TablePanel,
  TimeSeriesPanel,
  BlockingTreePanel
} from '../components/panels'
import type { DateRange, BlockingNode } from '../services/analyticsService'

export const Analytics = () => {
  const [serverId, setServerId] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState<DateRange>({
    start: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
    end: new Date()
  })
  const [selectedQuery, setSelectedQuery] = useState<Record<string, unknown> | null>(null)

  const {
    runningQueries,
    blockingChains,
    topDuration,
    topCpu,
    topIO,
    byDatabase,
    byLogin,
    byHost,
    byApplication,
    byWaitType,
    queryCountSeries
  } = useAnalyticsData(serverId, dateRange)

  const handleQueryClick = (query: Record<string, unknown> | BlockingNode) => {
    setSelectedQuery(query as Record<string, unknown>)
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Query Analytics</h1>
        <div className="flex items-center gap-4">
          <ServerSelector value={serverId} onChange={setServerId} />
          <DateRangePicker value={dateRange} onChange={setDateRange} />
        </div>
      </div>

      {!serverId ? (
        <div className="text-center py-16 text-gray-500 bg-white rounded-lg border border-gray-200">
          <div className="text-lg mb-2">Select a server to view query analytics</div>
          <div className="text-sm">Choose a monitored SQL Server from the dropdown above</div>
        </div>
      ) : (
        <>
          {/* Row 1: Blocking Chains + Running Queries */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BlockingTreePanel
              title="Blocking Chains"
              chains={blockingChains.data?.chains}
              totalBlocked={blockingChains.data?.total_blocked_sessions}
              isLoading={blockingChains.isLoading}
              error={blockingChains.error as Error | undefined}
              onQueryClick={handleQueryClick}
              height={320}
            />
            <TablePanel
              title="Currently Running Queries"
              subtitle={runningQueries.data?.collected_at
                ? `Updated ${new Date(runningQueries.data.collected_at).toLocaleTimeString()}`
                : undefined}
              columns={[
                { key: 'session_id', label: 'SPID', sortable: true, width: 60 },
                { key: 'duration_ms', label: 'Duration', sortable: true, width: 80,
                  render: (v) => v ? `${((v as number) / 1000).toFixed(1)}s` : '-' },
                { key: 'database_name', label: 'Database', sortable: true, width: 100 },
                { key: 'login_name', label: 'Login', sortable: true, width: 100 },
                { key: 'status', label: 'Status', sortable: true, width: 80 },
                { key: 'query_text', label: 'Query', sortable: false,
                  render: (v) => (v as string)?.slice(0, 50) || '-' }
              ]}
              rows={runningQueries.data?.rows}
              isLoading={runningQueries.isLoading}
              error={runningQueries.error as Error | undefined}
              onRowClick={handleQueryClick}
              height={320}
            />
          </div>

          {/* Row 2: Top Queries */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <BarPanel
              title="Top 10 by Duration"
              data={topDuration.data?.data}
              isLoading={topDuration.isLoading}
              error={topDuration.error as Error | undefined}
              color="#ef4444"
              unit="ms"
            />
            <BarPanel
              title="Top 10 by CPU"
              data={topCpu.data?.data}
              isLoading={topCpu.isLoading}
              error={topCpu.error as Error | undefined}
              color="#f59e0b"
              unit="ms"
            />
            <BarPanel
              title="Top 10 by I/O"
              data={topIO.data?.data}
              isLoading={topIO.isLoading}
              error={topIO.error as Error | undefined}
              color="#3b82f6"
              unit=""
            />
          </div>

          {/* Row 3: Breakdowns */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <PiePanel
              title="By Database"
              data={byDatabase.data?.data}
              isLoading={byDatabase.isLoading}
              error={byDatabase.error as Error | undefined}
              height={220}
            />
            <PiePanel
              title="By Login"
              data={byLogin.data?.data}
              isLoading={byLogin.isLoading}
              error={byLogin.error as Error | undefined}
              height={220}
            />
            <PiePanel
              title="By Host"
              data={byHost.data?.data}
              isLoading={byHost.isLoading}
              error={byHost.error as Error | undefined}
              height={220}
            />
            <PiePanel
              title="By Application"
              data={byApplication.data?.data}
              isLoading={byApplication.isLoading}
              error={byApplication.error as Error | undefined}
              height={220}
            />
          </div>

          {/* Row 4: Time Series + Wait Types */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <TimeSeriesPanel
                title="Query Count Over Time"
                data={queryCountSeries.data?.data}
                isLoading={queryCountSeries.isLoading}
                error={queryCountSeries.error as Error | undefined}
                color="#10b981"
                unit=" queries"
                height={280}
              />
            </div>
            <PiePanel
              title="Wait Types"
              data={byWaitType.data?.data}
              isLoading={byWaitType.isLoading}
              error={byWaitType.error as Error | undefined}
              height={280}
            />
          </div>
        </>
      )}

      {/* Query Detail Modal */}
      <QueryDetailModal
        query={selectedQuery}
        onClose={() => setSelectedQuery(null)}
      />
    </div>
  )
}
