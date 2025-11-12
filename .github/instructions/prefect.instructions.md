---
applyTo: '**/flows/**/*.py,**/tasks/**/*.py'
description: 'Prefect workflow and task development guidelines for autotune-app'
---

# Prefect Workflow Development Guidelines

## Overview

This project uses Prefect for workflow orchestration. Prefect manages the autotune analysis pipeline, including data loading, processing, and profile synchronization.

## Core Principles

### Task Design
- **Single Responsibility**: Each task should do one thing well
- **Idempotent**: Tasks should produce the same result when run multiple times with the same inputs
- **Stateless**: Tasks should not rely on shared state or global variables
- **Composable**: Tasks should be easily combined into flows
- **Testable**: Tasks should be easily testable in isolation

### Flow Design
- **Clear Purpose**: Each flow should have a clear, well-defined purpose
- **Modular**: Break complex workflows into smaller, manageable tasks
- **Error Handling**: Handle errors gracefully with retries and fallbacks
- **Observable**: Use logging and monitoring to track flow execution
- **Configurable**: Use parameters for flexibility

## Task Best Practices

### Task Definition
Use the `@task` decorator with appropriate settings.

Example:
```python
from prefect import task, get_run_logger
from typing import Dict, Any, Optional
import requests
from datetime import timedelta


@task(
    name="load-nightscout-data",
    description="Load historical data from Nightscout API",
    retries=3,
    retry_delay_seconds=60,
    timeout_seconds=300,
    cache_key_fn=lambda context, params: f"{params['url']}_{params['days']}",
    cache_expiration=timedelta(hours=1)
)
def load_nightscout_data(
    url: str,
    api_secret: str,
    days: int = 7
) -> Dict[str, Any]:
    """
    Load Nightscout data for specified number of days.
    
    Args:
        url: Nightscout URL
        api_secret: API secret for authentication
        days: Number of days of data to load
        
    Returns:
        Dict containing entries and treatments
        
    Raises:
        requests.HTTPError: If API request fails
    """
    logger = get_run_logger()
    logger.info(f"Loading {days} days of data from Nightscout")
    
    try:
        # Implementation here
        data = fetch_data(url, api_secret, days)
        logger.info(f"Successfully loaded {len(data['entries'])} entries")
        return data
    except requests.HTTPError as e:
        logger.error(f"Failed to load Nightscout data: {e}")
        raise
```

### Task Logging
Use Prefect's logging instead of print statements.

```python
from prefect import task, get_run_logger


@task
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Nightscout data."""
    logger = get_run_logger()
    
    # GOOD: Use Prefect logger
    logger.info(f"Processing {len(data)} items")
    logger.debug(f"Data keys: {data.keys()}")
    
    # BAD: Don't use print
    # print(f"Processing {len(data)} items")  # NEVER DO THIS
    
    return processed_data
```

### Task Retries
Configure retries for tasks that may fail transiently.

```python
from prefect import task
from datetime import timedelta


@task(
    retries=3,
    retry_delay_seconds=60,  # Wait 60 seconds between retries
    retry_jitter_factor=0.5  # Add random jitter to retry delays
)
def fetch_api_data(url: str) -> Dict[str, Any]:
    """Fetch data from API with automatic retries."""
    # This will retry up to 3 times if it fails
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

### Task Caching
Use task caching to avoid recomputing expensive operations.

```python
from prefect import task
from datetime import timedelta
from typing import Dict, Any


def cache_key_from_date(context, params):
    """Generate cache key based on date parameter."""
    return f"data_{params['date']}"


@task(
    cache_key_fn=cache_key_from_date,
    cache_expiration=timedelta(hours=24)
)
def load_historical_data(date: str) -> Dict[str, Any]:
    """
    Load historical data for a specific date.
    
    Results are cached for 24 hours based on the date.
    """
    # Expensive operation that we want to cache
    return fetch_data_for_date(date)
```

### Task Error Handling
Handle errors appropriately within tasks.

```python
from prefect import task, get_run_logger
from typing import Optional


@task
def safe_process_profile(profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process profile with error handling.
    
    Returns None if processing fails rather than raising exception.
    """
    logger = get_run_logger()
    
    try:
        validated_profile = validate_profile(profile)
        processed_profile = process_profile(validated_profile)
        return processed_profile
    except ValidationError as e:
        logger.error(f"Profile validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing profile: {e}", exc_info=True)
        return None
```

## Flow Best Practices

### Flow Definition
Define flows with clear parameters and documentation.

Example:
```python
from prefect import flow, get_run_logger
from typing import Optional
from datetime import datetime


@flow(
    name="autotune-analysis",
    description="Run autotune analysis on Nightscout data",
    version="1.0.0",
    timeout_seconds=3600
)
def autotune_analysis_flow(
    nightscout_url: str,
    api_secret: str,
    days: int = 7,
    profile_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run complete autotune analysis workflow.
    
    Args:
        nightscout_url: Nightscout URL
        api_secret: API secret for authentication
        days: Number of days of historical data to analyze
        profile_name: Name of profile to update (uses default if None)
        
    Returns:
        Dict containing autotune results
        
    Raises:
        ValueError: If configuration is invalid
        HTTPError: If API requests fail
    """
    logger = get_run_logger()
    logger.info(f"Starting autotune analysis for {days} days")
    
    # Load data
    data = load_nightscout_data(nightscout_url, api_secret, days)
    
    # Run autotune
    results = run_autotune_analysis(data, profile_name)
    
    # Sync results
    if results:
        sync_profile_to_nightscout(nightscout_url, api_secret, results)
    
    logger.info("Autotune analysis completed successfully")
    return results
```

### Flow Parameters
Use flow parameters for configuration.

```python
from prefect import flow
from pydantic import BaseModel, Field


class AutotuneConfig(BaseModel):
    """Configuration for autotune flow."""
    nightscout_url: str = Field(..., description="Nightscout URL")
    days: int = Field(7, ge=1, le=30, description="Days of data to analyze")
    min_entries: int = Field(100, description="Minimum entries required")
    

@flow
def autotune_flow(config: AutotuneConfig) -> Dict[str, Any]:
    """
    Run autotune with validated configuration.
    
    Args:
        config: Autotune configuration object
        
    Returns:
        Analysis results
    """
    # Configuration is validated by pydantic
    return run_analysis(config)
```

### Subflows
Break complex workflows into subflows.

```python
from prefect import flow, task


@flow(name="data-preparation")
def prepare_data_subflow(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for analysis (subflow)."""
    validated = validate_data(raw_data)
    cleaned = clean_data(validated)
    transformed = transform_data(cleaned)
    return transformed


@flow(name="autotune-main")
def main_autotune_flow(nightscout_url: str, api_secret: str) -> Dict[str, Any]:
    """Main autotune flow."""
    # Load data
    raw_data = load_nightscout_data(nightscout_url, api_secret)
    
    # Use subflow for data preparation
    prepared_data = prepare_data_subflow(raw_data)
    
    # Continue with analysis
    results = run_autotune(prepared_data)
    
    return results
```

### Flow State Handling
Handle different flow states appropriately.

```python
from prefect import flow, task, get_run_logger
from prefect.states import State


@flow
def monitored_autotune_flow(
    nightscout_url: str,
    api_secret: str
) -> Dict[str, Any]:
    """Flow with state monitoring."""
    logger = get_run_logger()
    
    try:
        # Run tasks
        data = load_nightscout_data(nightscout_url, api_secret)
        results = run_autotune(data)
        
        # Success
        logger.info("Flow completed successfully")
        return results
        
    except Exception as e:
        # Failure
        logger.error(f"Flow failed: {e}", exc_info=True)
        # Send notification or alert
        notify_failure(str(e))
        raise
```

## Deployment Best Practices

### Deployment Configuration
Configure deployments for scheduled runs.

```python
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule


deployment = Deployment.build_from_flow(
    flow=autotune_analysis_flow,
    name="nightly-autotune",
    schedule=CronSchedule(cron="0 2 * * *"),  # Run at 2 AM daily
    work_queue_name="autotune-queue",
    tags=["autotune", "nightly"],
    parameters={
        "days": 7,
        "profile_name": "Default"
    }
)

deployment.apply()
```

### Work Queues
Use work queues to organize and prioritize flows.

```python
from prefect.client import get_client


async def create_work_queues():
    """Create work queues for different job types."""
    async with get_client() as client:
        # High priority queue for manual runs
        await client.create_work_queue(
            name="autotune-manual",
            priority=100
        )
        
        # Normal priority for scheduled runs
        await client.create_work_queue(
            name="autotune-scheduled",
            priority=50
        )
```

## Testing Prefect Workflows

### Testing Tasks
Test tasks as regular Python functions.

```python
import pytest
from unittest.mock import Mock, patch


def test_load_nightscout_data():
    """Test loading Nightscout data task."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"entries": []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = load_nightscout_data.fn(
            "https://test.herokuapp.com",
            "secret",
            days=7
        )
        
        assert result is not None
        assert "entries" in result
```

### Testing Flows
Test flows with Prefect's testing utilities.

```python
from prefect.testing.utilities import prefect_test_harness
import pytest


def test_autotune_flow():
    """Test autotune flow execution."""
    with prefect_test_harness():
        result = autotune_analysis_flow(
            nightscout_url="https://test.herokuapp.com",
            api_secret="test-secret",
            days=1
        )
        
        assert result is not None
        assert "basal" in result
```

## Monitoring and Observability

### Logging Best Practices
- Use structured logging with context
- Log at appropriate levels (INFO, DEBUG, WARNING, ERROR)
- Include relevant information (IDs, counts, durations)
- Don't log sensitive data (API secrets, personal data)

### Metrics and Monitoring
- Track flow run durations
- Monitor task success/failure rates
- Alert on consecutive failures
- Track data quality metrics

Example:
```python
from prefect import flow, task, get_run_logger
from datetime import datetime


@task
def load_data_with_metrics(url: str, api_secret: str) -> Dict[str, Any]:
    """Load data and track metrics."""
    logger = get_run_logger()
    start_time = datetime.now()
    
    data = load_nightscout_data(url, api_secret)
    
    duration = (datetime.now() - start_time).total_seconds()
    entry_count = len(data.get('entries', []))
    
    logger.info(
        f"Data loaded: {entry_count} entries in {duration:.2f}s",
        extra={
            "duration_seconds": duration,
            "entry_count": entry_count
        }
    )
    
    return data
```

## Common Pitfalls to Avoid

- ❌ Using print() instead of Prefect logging
- ❌ Not configuring retries for API calls
- ❌ Storing state in global variables
- ❌ Not handling task failures gracefully
- ❌ Creating tasks that are too large or complex
- ❌ Not using task caching for expensive operations
- ❌ Hardcoding configuration in tasks
- ❌ Not testing tasks in isolation
- ❌ Logging sensitive data (API secrets, personal health data)
- ❌ Not documenting task parameters and return values

## References

- [Prefect Documentation](https://docs.prefect.io/)
- [Prefect Best Practices](https://docs.prefect.io/2.latest/guides/best-practices/)
- [Prefect Task Guide](https://docs.prefect.io/2.latest/concepts/tasks/)
- [Prefect Flow Guide](https://docs.prefect.io/2.latest/concepts/flows/)
