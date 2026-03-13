SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

ALTER TABLE [dbo].[finance_staging_cost_details]
    ADD [element_resourceGroupName] NVARCHAR(512) NULL;

ALTER TABLE [dbo].[finance_staging_cost_details]
    ADD [element_location] NVARCHAR(256) NULL;

ALTER TABLE [dbo].[finance_staging_cost_details]
    ADD [element_provider] NVARCHAR(256) NULL;
