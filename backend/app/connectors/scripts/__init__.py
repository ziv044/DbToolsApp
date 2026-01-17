"""SQL Server deployment scripts for monitoring objects."""

# Current deployment version
DEPLOYMENT_VERSION = "1.0.0"

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
