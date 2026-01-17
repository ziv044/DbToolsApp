"""SQL Server deployment scripts for monitoring objects."""

# Current deployment version
DEPLOYMENT_VERSION = "1.1.0"

# Schema creation script
CREATE_SCHEMA = """
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'DbTools')
BEGIN
    EXEC('CREATE SCHEMA DbTools')
END
"""

# Config table creation script
CREATE_CONFIG_TABLE = """
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'DbTools.Config') AND type = 'U')
BEGIN
    CREATE TABLE DbTools.Config (
        [Key] VARCHAR(100) PRIMARY KEY,
        [Value] NVARCHAR(MAX),
        UpdatedAt DATETIME DEFAULT GETDATE()
    )

    -- Insert version info
    INSERT INTO DbTools.Config ([Key], [Value]) VALUES ('Version', '{version}')
    INSERT INTO DbTools.Config ([Key], [Value]) VALUES ('DeployedAt', CONVERT(VARCHAR(30), GETUTCDATE(), 126) + 'Z')
END
ELSE
BEGIN
    -- Update version if exists
    IF EXISTS (SELECT 1 FROM DbTools.Config WHERE [Key] = 'Version')
        UPDATE DbTools.Config SET [Value] = '{version}', UpdatedAt = GETDATE() WHERE [Key] = 'Version'
    ELSE
        INSERT INTO DbTools.Config ([Key], [Value]) VALUES ('Version', '{version}')

    IF EXISTS (SELECT 1 FROM DbTools.Config WHERE [Key] = 'DeployedAt')
        UPDATE DbTools.Config SET [Value] = CONVERT(VARCHAR(30), GETUTCDATE(), 126) + 'Z', UpdatedAt = GETDATE() WHERE [Key] = 'DeployedAt'
    ELSE
        INSERT INTO DbTools.Config ([Key], [Value]) VALUES ('DeployedAt', CONVERT(VARCHAR(30), GETUTCDATE(), 126) + 'Z')
END
""".format(version=DEPLOYMENT_VERSION)

# Stored procedure to get server info and basic metrics
CREATE_SP_GET_SERVER_INFO = """
CREATE OR ALTER PROCEDURE DbTools.GetServerInfo
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        SERVERPROPERTY('MachineName') AS MachineName,
        SERVERPROPERTY('ServerName') AS ServerName,
        SERVERPROPERTY('InstanceName') AS InstanceName,
        SERVERPROPERTY('ProductVersion') AS ProductVersion,
        SERVERPROPERTY('ProductMajorVersion') AS ProductMajorVersion,
        SERVERPROPERTY('Edition') AS Edition,
        SERVERPROPERTY('ProductLevel') AS ProductLevel,
        @@VERSION AS FullVersion
END
"""

# Stored procedure to collect CPU metrics
CREATE_SP_COLLECT_CPU = """
CREATE OR ALTER PROCEDURE DbTools.CollectCpuMetrics
AS
BEGIN
    SET NOCOUNT ON

    -- Get CPU usage from ring buffers
    SELECT TOP 1
        record.value('(./Record/@id)[1]', 'int') AS record_id,
        record.value('(./Record/SchedulerMonitorEvent/SystemHealth/ProcessUtilization)[1]', 'int') AS SqlProcessUtilization,
        record.value('(./Record/SchedulerMonitorEvent/SystemHealth/SystemIdle)[1]', 'int') AS SystemIdle,
        100 - record.value('(./Record/SchedulerMonitorEvent/SystemHealth/SystemIdle)[1]', 'int') - record.value('(./Record/SchedulerMonitorEvent/SystemHealth/ProcessUtilization)[1]', 'int') AS OtherProcessUtilization
    FROM (
        SELECT CAST(record AS XML) AS record
        FROM sys.dm_os_ring_buffers
        WHERE ring_buffer_type = N'RING_BUFFER_SCHEDULER_MONITOR'
        AND record LIKE '%<SystemHealth>%'
    ) AS t
    ORDER BY record_id DESC
END
"""

# Stored procedure to collect memory metrics
CREATE_SP_COLLECT_MEMORY = """
CREATE OR ALTER PROCEDURE DbTools.CollectMemoryMetrics
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        physical_memory_kb / 1024 AS TotalPhysicalMemoryMB,
        available_physical_memory_kb / 1024 AS AvailablePhysicalMemoryMB,
        total_page_file_kb / 1024 AS TotalPageFileMB,
        available_page_file_kb / 1024 AS AvailablePageFileMB,
        system_memory_state_desc AS MemoryState
    FROM sys.dm_os_sys_memory
END
"""

# Stored procedure to collect wait stats
CREATE_SP_COLLECT_WAITS = """
CREATE OR ALTER PROCEDURE DbTools.CollectWaitStats
AS
BEGIN
    SET NOCOUNT ON

    SELECT TOP 20
        wait_type AS WaitType,
        wait_time_ms AS WaitTimeMs,
        max_wait_time_ms AS MaxWaitTimeMs,
        signal_wait_time_ms AS SignalWaitTimeMs,
        waiting_tasks_count AS WaitingTasksCount
    FROM sys.dm_os_wait_stats
    WHERE wait_type NOT IN (
        'CLR_SEMAPHORE', 'LAZYWRITER_SLEEP', 'RESOURCE_QUEUE', 'SLEEP_TASK',
        'SLEEP_SYSTEMTASK', 'SQLTRACE_BUFFER_FLUSH', 'WAITFOR', 'LOGMGR_QUEUE',
        'CHECKPOINT_QUEUE', 'REQUEST_FOR_DEADLOCK_SEARCH', 'XE_TIMER_EVENT',
        'BROKER_TO_FLUSH', 'BROKER_TASK_STOP', 'CLR_MANUAL_EVENT', 'CLR_AUTO_EVENT',
        'DISPATCHER_QUEUE_SEMAPHORE', 'FT_IFTS_SCHEDULER_IDLE_WAIT', 'XE_DISPATCHER_WAIT',
        'XE_DISPATCHER_JOIN', 'SQLTRACE_INCREMENTAL_FLUSH_SLEEP', 'ONDEMAND_TASK_QUEUE',
        'BROKER_EVENTHANDLER', 'SLEEP_BPOOL_FLUSH', 'DIRTY_PAGE_POLL', 'HADR_FILESTREAM_IOMGR_IOCOMPLETION'
    )
    AND waiting_tasks_count > 0
    ORDER BY wait_time_ms DESC
END
"""

# Stored procedure to collect database info
CREATE_SP_COLLECT_DATABASES = """
CREATE OR ALTER PROCEDURE DbTools.CollectDatabaseInfo
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        d.database_id AS DatabaseId,
        d.name AS DatabaseName,
        d.state_desc AS State,
        d.recovery_model_desc AS RecoveryModel,
        d.compatibility_level AS CompatibilityLevel,
        CAST(SUM(mf.size) * 8.0 / 1024 AS DECIMAL(18,2)) AS SizeMB
    FROM sys.databases d
    LEFT JOIN sys.master_files mf ON d.database_id = mf.database_id
    WHERE d.database_id > 4 -- Skip system databases
    GROUP BY d.database_id, d.name, d.state_desc, d.recovery_model_desc, d.compatibility_level
    ORDER BY d.name
END
"""

# Stored procedure to collect connection metrics
CREATE_SP_COLLECT_CONNECTIONS = """
CREATE OR ALTER PROCEDURE DbTools.CollectConnectionMetrics
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        COUNT(*) AS TotalConnections,
        SUM(CASE WHEN is_user_process = 1 THEN 1 ELSE 0 END) AS UserConnections,
        SUM(CASE WHEN is_user_process = 0 THEN 1 ELSE 0 END) AS SystemConnections,
        MAX(login_time) AS LastLoginTime
    FROM sys.dm_exec_sessions
END
"""

# Stored procedure to collect performance counters
CREATE_SP_COLLECT_PERF_COUNTERS = """
CREATE OR ALTER PROCEDURE DbTools.CollectPerfCounters
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        object_name AS ObjectName,
        counter_name AS CounterName,
        instance_name AS InstanceName,
        cntr_value AS CounterValue,
        cntr_type AS CounterType
    FROM sys.dm_os_performance_counters
    WHERE counter_name IN (
        'Batch Requests/sec',
        'SQL Compilations/sec',
        'SQL Re-Compilations/sec',
        'User Connections',
        'Page life expectancy',
        'Buffer cache hit ratio',
        'Transactions/sec',
        'Lock Waits/sec',
        'Full Scans/sec',
        'Index Searches/sec'
    )
END
"""

# Stored procedure to collect disk I/O metrics
CREATE_SP_COLLECT_DISK_IO = """
CREATE OR ALTER PROCEDURE DbTools.CollectDiskIO
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        DB_NAME(database_id) AS DatabaseName,
        file_id AS FileId,
        num_of_reads AS NumReads,
        num_of_writes AS NumWrites,
        num_of_bytes_read AS BytesRead,
        num_of_bytes_written AS BytesWritten,
        io_stall_read_ms AS ReadStallMs,
        io_stall_write_ms AS WriteStallMs,
        size_on_disk_bytes AS SizeOnDiskBytes
    FROM sys.dm_io_virtual_file_stats(NULL, NULL)
    WHERE database_id > 4 -- Skip system databases
END
"""

# Stored procedure to collect all metrics at once
CREATE_SP_COLLECT_ALL_METRICS = """
CREATE OR ALTER PROCEDURE DbTools.CollectAllMetrics
AS
BEGIN
    SET NOCOUNT ON

    -- CPU metrics
    DECLARE @SqlCpu INT, @SystemIdle INT
    SELECT TOP 1
        @SqlCpu = record.value('(./Record/SchedulerMonitorEvent/SystemHealth/ProcessUtilization)[1]', 'int'),
        @SystemIdle = record.value('(./Record/SchedulerMonitorEvent/SystemHealth/SystemIdle)[1]', 'int')
    FROM (
        SELECT CAST(record AS XML) AS record
        FROM sys.dm_os_ring_buffers
        WHERE ring_buffer_type = N'RING_BUFFER_SCHEDULER_MONITOR'
        AND record LIKE '%<SystemHealth>%'
    ) AS t

    -- Memory metrics
    DECLARE @TotalMemoryMB BIGINT, @AvailableMemoryMB BIGINT, @MemoryPercent DECIMAL(5,2)
    SELECT
        @TotalMemoryMB = physical_memory_kb / 1024,
        @AvailableMemoryMB = available_physical_memory_kb / 1024,
        @MemoryPercent = (physical_memory_kb - available_physical_memory_kb) * 100.0 / physical_memory_kb
    FROM sys.dm_os_sys_memory

    -- Connection count
    DECLARE @ConnectionCount INT
    SELECT @ConnectionCount = COUNT(*) FROM sys.dm_exec_sessions WHERE is_user_process = 1

    -- Performance counters
    DECLARE @BatchRequestsSec BIGINT, @PageLifeExpectancy INT
    SELECT @BatchRequestsSec = cntr_value FROM sys.dm_os_performance_counters WHERE counter_name = 'Batch Requests/sec'
    SELECT @PageLifeExpectancy = cntr_value FROM sys.dm_os_performance_counters WHERE counter_name = 'Page life expectancy' AND object_name LIKE '%Buffer Manager%'

    -- Blocked processes
    DECLARE @BlockedProcesses INT
    SELECT @BlockedProcesses = COUNT(*) FROM sys.dm_exec_requests WHERE blocking_session_id > 0

    -- Return all metrics
    SELECT
        @SqlCpu AS SqlCpuPercent,
        @SystemIdle AS SystemIdlePercent,
        100 - ISNULL(@SystemIdle, 0) - ISNULL(@SqlCpu, 0) AS OtherCpuPercent,
        @TotalMemoryMB AS TotalMemoryMB,
        @AvailableMemoryMB AS AvailableMemoryMB,
        @MemoryPercent AS MemoryUsedPercent,
        @ConnectionCount AS ConnectionCount,
        @BatchRequestsSec AS BatchRequestsSec,
        @PageLifeExpectancy AS PageLifeExpectancy,
        @BlockedProcesses AS BlockedProcesses,
        GETUTCDATE() AS CollectedAtUtc
END
"""

# Stored procedure to get deployment status
CREATE_SP_GET_DEPLOYMENT_STATUS = """
CREATE OR ALTER PROCEDURE DbTools.GetDeploymentStatus
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        [Key],
        [Value],
        UpdatedAt
    FROM DbTools.Config
    WHERE [Key] IN ('Version', 'DeployedAt')
END
"""

# All scripts in deployment order
DEPLOYMENT_SCRIPTS = [
    ('Create Schema', CREATE_SCHEMA),
    ('Create Config Table', CREATE_CONFIG_TABLE),
    ('Create GetServerInfo SP', CREATE_SP_GET_SERVER_INFO),
    ('Create CollectCpuMetrics SP', CREATE_SP_COLLECT_CPU),
    ('Create CollectMemoryMetrics SP', CREATE_SP_COLLECT_MEMORY),
    ('Create CollectWaitStats SP', CREATE_SP_COLLECT_WAITS),
    ('Create CollectDatabaseInfo SP', CREATE_SP_COLLECT_DATABASES),
    ('Create CollectConnectionMetrics SP', CREATE_SP_COLLECT_CONNECTIONS),
    ('Create CollectPerfCounters SP', CREATE_SP_COLLECT_PERF_COUNTERS),
    ('Create CollectDiskIO SP', CREATE_SP_COLLECT_DISK_IO),
    ('Create CollectAllMetrics SP', CREATE_SP_COLLECT_ALL_METRICS),
    ('Create GetDeploymentStatus SP', CREATE_SP_GET_DEPLOYMENT_STATUS),
]

# Script to check required permissions
CHECK_PERMISSIONS = """
SELECT
    CASE WHEN HAS_PERMS_BY_NAME(null, null, 'CREATE PROCEDURE') = 1 THEN 1 ELSE 0 END AS CanCreateProcedure,
    CASE WHEN HAS_PERMS_BY_NAME(null, null, 'CREATE TABLE') = 1 THEN 1 ELSE 0 END AS CanCreateTable,
    CASE WHEN HAS_PERMS_BY_NAME(null, null, 'CREATE SCHEMA') = 1 THEN 1 ELSE 0 END AS CanCreateSchema,
    CASE WHEN HAS_PERMS_BY_NAME(null, null, 'VIEW SERVER STATE') = 1 THEN 1 ELSE 0 END AS CanViewServerState
"""
