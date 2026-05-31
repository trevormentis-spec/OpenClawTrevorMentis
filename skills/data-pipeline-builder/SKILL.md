# data-pipeline-builder

Build and manage ETL/data pipelines for AI agents. Extract, transform, load data between databases, APIs, and file systems.

## Overview

A skill for creating and managing data pipelines that move and transform data across different sources and destinations.

## Features

- **Source Connectors**: Connect to databases, APIs, files, S3, GCS
- **Data Transformation**: Apply filters, mappings, aggregations
- **Scheduling**: Cron-based or event-triggered pipelines
- **Error Handling**: Retry logic, dead letter queues
- **Data Validation**: Schema validation, data quality checks
- **Monitoring**: Pipeline status, throughput, error rates
- **Incremental Sync**: Support for CDC (Change Data Capture)

## Commands

### Create Pipeline

```
create pipeline from mysql to postgres
```

### Run Pipeline

```
run etl-job daily-sales-report
```

### Monitor Pipeline

```
check pipeline health
```

## Use Cases

- Database synchronization
- API data extraction
- File processing and conversion
- Data warehousing
- Report generation
- Analytics data preparation

## Requirements

- Node.js 18+
- Python 3.8+ (for data processing)
- Source/destination connectors as needed
