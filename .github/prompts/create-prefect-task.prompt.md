---
mode: 'agent'
model: 'Claude Sonnet 4.5'
tools: ['codebase', 'edit/editFiles', 'search']
description: 'Create a new Prefect task or flow with proper structure and best practices'
---

# Create Prefect Task or Flow

You are creating a new Prefect task or flow for the autotune-app project. Follow Prefect best practices and project conventions.

## Task Creation

### When to Create a Task
- Single, focused operation (load data, process data, save data)
- Operation that might fail and need retries (API calls, I/O operations)
- Expensive operation that should be cached
- Operation that should be logged and monitored

### Task Structure

```python
from prefect import task, get_run_logger
from typing import Dict, Any, Optional
from datetime import timedelta


@task(
    name="descriptive-task-name",
    description="Clear description of what this task does",
    retries=3,
    retry_delay_seconds=60,
    timeout_seconds=300,
    cache_key_fn=None,  # Optional: function to generate cache key
    cache_expiration=None,  # Optional: timedelta for cache expiration
    tags=["category", "subcategory"]
)
def my_task(
    param1: str,
    param2: int,
    optional_param: Optional[str] = None
) -> Dict[str, Any]:
    """
    Brief description of what the task does.
    
    Detailed explanation of the task's purpose, behavior, and any
    important considerations.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
        optional_param: Description of optional parameter
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When and why this is raised
        requests.HTTPError: When API calls fail
    
    Example:
        >>> result = my_task("input", 42)
        >>> print(result)
        {'status': 'success', 'data': [...]}
    """
    logger = get_run_logger()
    logger.info(f"Starting task with param1={param1}, param2={param2}")
    
    try:
        # Task implementation
        result = perform_operation(param1, param2, optional_param)
        
        logger.info(f"Task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Task failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
```

### Task Best Practices

1. **Naming**
   - Use descriptive, lowercase names with hyphens
   - Include action verb (load, process, sync, validate)
   - Example: `load-nightscout-data`, `run-autotune-analysis`

2. **Parameters**
   - Use type hints for all parameters
   - Provide defaults for optional parameters
   - Keep parameter count reasonable (< 5 if possible)
   - Use dataclasses or TypedDict for complex parameters

3. **Return Values**
   - Always return structured data (dict, dataclass, list)
   - Document return value structure in docstring
   - Return None only if truly no result

4. **Error Handling**
   - Let exceptions propagate for task retry logic
   - Use specific exception types
   - Log errors with context before raising
   - Document expected exceptions

5. **Logging**
   - Use `get_run_logger()` for Prefect logging
   - Log start, success, and failure
   - Log important intermediate steps
   - Include relevant context (IDs, counts, durations)
   - Never log sensitive data (API secrets, personal health data)

6. **Retries**
   - Configure retries for operations that might fail transiently
   - Use appropriate retry delays (exponential backoff for APIs)
   - Add retry jitter to avoid thundering herd

7. **Caching**
   - Cache expensive operations that produce same results
   - Define cache key function based on inputs
   - Set appropriate cache expiration
   - Document caching behavior

## Flow Creation

### When to Create a Flow
- Orchestrate multiple tasks into a workflow
- Define business process (e.g., "run autotune analysis")
- Handle complex error scenarios
- Coordinate parallel operations

### Flow Structure

```python
from prefect import flow, get_run_logger
from typing import Dict, Any, Optional
from datetime import timedelta


@flow(
    name="descriptive-flow-name",
    description="Clear description of what this flow does",
    version="1.0.0",
    timeout_seconds=3600,
    retries=0,  # Usually don't retry entire flows
    log_prints=True
)
def my_flow(
    param1: str,
    param2: int,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Brief description of what the flow does.
    
    Detailed explanation of the workflow, steps involved, and
    expected outcomes.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
        config: Optional configuration dictionary
    
    Returns:
        Dictionary containing flow results:
            {
                'status': 'success' | 'failed',
                'data': {...},
                'metrics': {...}
            }
    
    Raises:
        ValueError: If configuration is invalid
        RuntimeError: If critical task fails
    
    Example:
        >>> result = my_flow("input", 42)
        >>> print(result['status'])
        'success'
    """
    logger = get_run_logger()
    logger.info(f"Starting flow with param1={param1}")
    
    # Validate configuration
    if config:
        validate_config(config)
    
    try:
        # Step 1: Load data
        data = load_data_task(param1)
        logger.info(f"Loaded {len(data)} items")
        
        # Step 2: Process data
        processed = process_data_task(data, param2)
        logger.info("Data processing complete")
        
        # Step 3: Save results
        save_results_task(processed)
        
        # Return success
        return {
            'status': 'success',
            'data': processed,
            'metrics': {
                'items_processed': len(processed),
                'param1': param1,
                'param2': param2
            }
        }
        
    except Exception as e:
        logger.error(f"Flow failed: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__
        }
```

### Flow Best Practices

1. **Structure**
   - Clear beginning, middle, and end
   - Logical task sequence
   - Handle errors gracefully
   - Return structured results

2. **Error Handling**
   - Catch exceptions at flow level
   - Decide whether to retry or fail
   - Log comprehensive error information
   - Return error status in results

3. **Task Composition**
   - Break workflow into logical tasks
   - Pass results between tasks explicitly
   - Use subflows for complex sub-workflows
   - Keep flows focused on orchestration

4. **Parameters**
   - Use clear, descriptive parameter names
   - Validate parameters at start of flow
   - Use configuration objects for complex config
   - Document all parameters thoroughly

5. **Logging**
   - Log flow start and completion
   - Log major workflow steps
   - Include metrics and statistics
   - Provide progress updates for long operations

## File Organization

### Task Files
Location: `src/autotune_app/tasks/`

File naming: `{category}_tasks.py`

Examples:
- `data_loading_tasks.py` - Tasks for loading data
- `autotune_tasks.py` - Tasks for autotune operations
- `nightscout_tasks.py` - Tasks for Nightscout API

### Flow Files
Location: `src/autotune_app/flows/`

File naming: `{workflow_name}_flow.py`

Examples:
- `autotune_analysis_flow.py` - Main autotune workflow
- `profile_sync_flow.py` - Profile synchronization workflow

### Module Structure
```python
"""
Module docstring describing the tasks/flows in this file.

This module contains tasks for [purpose] including:
- Task 1: [brief description]
- Task 2: [brief description]
"""

from prefect import task, flow, get_run_logger
from typing import Dict, Any, List, Optional
import logging

# Import project modules
from autotune_app.services import SomeService
from autotune_app.models import SomeModel

# Module-level logger (for non-Prefect code)
logger = logging.getLogger(__name__)


# Constants
DEFAULT_TIMEOUT = 300
MAX_RETRIES = 3


# Tasks
@task(...)
def task_one(...):
    """Docstring"""
    pass


@task(...)
def task_two(...):
    """Docstring"""
    pass


# Flows
@flow(...)
def main_flow(...):
    """Docstring"""
    pass
```

## Testing

### Task Testing
```python
import pytest
from unittest.mock import Mock, patch
from autotune_app.tasks.my_tasks import my_task


def test_my_task_success():
    """Test task with successful execution."""
    result = my_task.fn("input", 42)  # Use .fn to call without Prefect context
    
    assert result is not None
    assert result['status'] == 'success'


def test_my_task_with_mocked_dependency():
    """Test task with mocked external dependency."""
    with patch('autotune_app.tasks.my_tasks.external_api') as mock_api:
        mock_api.return_value = {'data': 'mocked'}
        
        result = my_task.fn("input", 42)
        
        assert result['data'] == 'mocked'
        mock_api.assert_called_once()
```

### Flow Testing
```python
from prefect.testing.utilities import prefect_test_harness
from autotune_app.flows.my_flow import my_flow


def test_my_flow():
    """Test flow execution."""
    with prefect_test_harness():
        result = my_flow("input", 42)
        
        assert result['status'] == 'success'
        assert 'data' in result
```

## Checklist

- [ ] Task/flow has clear, descriptive name
- [ ] Comprehensive docstring with examples
- [ ] Type hints for all parameters and return values
- [ ] Appropriate retry configuration
- [ ] Proper error handling
- [ ] Prefect logging (not print statements)
- [ ] Sensitive data not logged
- [ ] Tests written and passing
- [ ] File placed in correct directory
- [ ] Module docstring updated

Ready to create a well-structured Prefect task or flow!
