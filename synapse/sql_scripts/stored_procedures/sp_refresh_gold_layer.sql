-- Stored Procedure: Refresh Gold Layer Statistics
-- Call after Databricks Gold transformations complete to update Synapse statistics

CREATE OR ALTER PROCEDURE [gold].[sp_refresh_gold_layer]
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @start_time DATETIME2 = SYSUTCDATETIME();
    DECLARE @table_name NVARCHAR(200);
    DECLARE @sql NVARCHAR(MAX);

    -- Update statistics on all gold external tables
    DECLARE table_cursor CURSOR FOR
    SELECT TABLE_SCHEMA + '.' + TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'gold'
      AND TABLE_TYPE = 'BASE TABLE';

    OPEN table_cursor;
    FETCH NEXT FROM table_cursor INTO @table_name;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @sql = 'UPDATE STATISTICS ' + QUOTENAME(PARSENAME(@table_name, 2)) + '.' + QUOTENAME(PARSENAME(@table_name, 1));

        BEGIN TRY
            EXEC sp_executesql @sql;
            PRINT 'Updated statistics for ' + @table_name;
        END TRY
        BEGIN CATCH
            PRINT 'Warning: Failed to update statistics for ' + @table_name + ': ' + ERROR_MESSAGE();
        END CATCH

        FETCH NEXT FROM table_cursor INTO @table_name;
    END

    CLOSE table_cursor;
    DEALLOCATE table_cursor;

    -- Log completion
    DECLARE @duration_seconds INT = DATEDIFF(SECOND, @start_time, SYSUTCDATETIME());
    PRINT 'Gold layer refresh completed in ' + CAST(@duration_seconds AS VARCHAR(10)) + ' seconds.';
END;
GO
