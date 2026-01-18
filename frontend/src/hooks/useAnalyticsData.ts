import { useQuery } from '@tanstack/react-query'
import { analyticsService, type DateRange } from '../services/analyticsService'

export function useAnalyticsData(serverId: string | null, dateRange: DateRange) {
  const enabled = !!serverId

  // Live data - refresh every 10 seconds
  const runningQueries = useQuery({
    queryKey: ['analytics', 'running', serverId],
    queryFn: () => analyticsService.getRunningQueries(serverId!),
    enabled,
    refetchInterval: 10_000,
    staleTime: 5_000
  })

  const blockingChains = useQuery({
    queryKey: ['analytics', 'blocking', serverId],
    queryFn: () => analyticsService.getBlockingChains(serverId!),
    enabled,
    refetchInterval: 10_000,
    staleTime: 5_000
  })

  // Historical data - no auto-refresh, depends on date range
  const topDuration = useQuery({
    queryKey: ['analytics', 'top', 'duration', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getTopQueries(serverId!, dateRange, 'duration'),
    enabled,
    staleTime: 30_000
  })

  const topCpu = useQuery({
    queryKey: ['analytics', 'top', 'cpu', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getTopQueries(serverId!, dateRange, 'cpu'),
    enabled,
    staleTime: 30_000
  })

  const topIO = useQuery({
    queryKey: ['analytics', 'top', 'io', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getTopQueries(serverId!, dateRange, 'io'),
    enabled,
    staleTime: 30_000
  })

  // Breakdowns
  const byDatabase = useQuery({
    queryKey: ['analytics', 'breakdown', 'database', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getBreakdown(serverId!, dateRange, 'database'),
    enabled,
    staleTime: 30_000
  })

  const byLogin = useQuery({
    queryKey: ['analytics', 'breakdown', 'login', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getBreakdown(serverId!, dateRange, 'login'),
    enabled,
    staleTime: 30_000
  })

  const byHost = useQuery({
    queryKey: ['analytics', 'breakdown', 'host', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getBreakdown(serverId!, dateRange, 'host'),
    enabled,
    staleTime: 30_000
  })

  const byApplication = useQuery({
    queryKey: ['analytics', 'breakdown', 'application', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getBreakdown(serverId!, dateRange, 'application'),
    enabled,
    staleTime: 30_000
  })

  const byWaitType = useQuery({
    queryKey: ['analytics', 'breakdown', 'wait-type', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getBreakdown(serverId!, dateRange, 'wait-type'),
    enabled,
    staleTime: 30_000
  })

  // Time series
  const queryCountSeries = useQuery({
    queryKey: ['analytics', 'timeseries', 'query-count', serverId, dateRange.start.getTime(), dateRange.end.getTime()],
    queryFn: () => analyticsService.getTimeSeries(serverId!, dateRange, 'query-count'),
    enabled,
    staleTime: 30_000
  })

  return {
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
  }
}
