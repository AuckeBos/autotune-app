# Clients and Services Implementation

This directory contains the core implementation of the Nightscout and Autotune clients and services.

## Structure

```
src/app/
├── clients/           # Low-level API clients
│   ├── nightscout_client.py   # Nightscout API client
│   └── autotune_client.py     # Autotune CLI wrapper
├── models/            # Pydantic data models
│   ├── nightscout.py          # Nightscout data structures
│   └── autotune.py            # Autotune data structures
└── services/          # High-level service layer
    ├── nightscout_service.py  # Nightscout service with validation
    └── autotune_service.py    # Autotune service with validation
```

## Components

### Clients (Low-Level)

#### NightscoutClient
Located in `clients/nightscout_client.py`

**Purpose**: Direct interaction with Nightscout API endpoints

**Key Methods**:
- `get_profile(profile_name)`: Load profile by name
- `get_entries(start_date, end_date)`: Load glucose entries
- `get_treatments(start_date, end_date)`: Load treatment entries
- `get_historical_data(days)`: Load all historical data for specified days
- `update_profile(profile_data, profile_name)`: Sync updated profile back to Nightscout

**Features**:
- HTTPS-only connections for security
- SHA1 hashed API secret authentication
- Automatic retry logic with exponential backoff
- Comprehensive error handling
- Structured logging

#### AutotuneClient
Located in `clients/autotune_client.py`

**Purpose**: Wrapper around the oref0-autotune command-line tool

**Key Methods**:
- `run_autotune(profile_data, entries, treatments, days)`: Execute autotune analysis
- `upload_profile(profile_data, nightscout_url, api_secret)`: Upload profile (if oref0-upload available)

**Features**:
- Temporary file management for autotune inputs/outputs
- Subprocess execution with timeout handling
- Result validation and error handling
- Structured logging of autotune execution

### Models (Data Validation)

#### Nightscout Models
Located in `models/nightscout.py`

**Pydantic Models**:
- `BasalScheduleEntry`: Single basal rate entry
- `CarbRatioEntry`: Single carb ratio entry
- `SensitivityEntry`: Single insulin sensitivity entry
- `TargetEntry`: Single target BG entry
- `ProfileStore`: Complete profile with all schedules
- `NightscoutProfile`: Full profile document with metadata
- `NightscoutEntry`: Glucose entry
- `NightscoutTreatment`: Treatment entry (insulin, carbs, etc.)
- `HistoricalData`: Container for entries and treatments with date range

**Validation**:
- Value range checking (e.g., glucose 20-600 mg/dL)
- Required field enforcement
- Type validation
- Automatic data coercion

#### Autotune Models
Located in `models/autotune.py`

**Pydantic Models**:
- `AutotuneBasalEntry`: Basal rate from autotune output
- `AutotuneCarbRatioEntry`: Carb ratio recommendation
- `AutotuneSensitivityEntry`: ISF recommendation
- `AutotuneResult`: Complete autotune output
- `AutotuneRecommendations`: Wrapped result with metadata

### Services (High-Level)

#### NightscoutService
Located in `services/nightscout_service.py`

**Purpose**: User-friendly wrapper around NightscoutClient with automatic validation

**Key Methods**:
- `get_profile(profile_name)`: Returns validated `NightscoutProfile` model
- `get_profile_store(profile_name)`: Returns validated `ProfileStore` model
- `get_historical_data(days)`: Returns validated `HistoricalData` model
- `sync_profile(profile_store, profile_name)`: Sync ProfileStore back to Nightscout

**Features**:
- Automatic Pydantic validation of all data
- Invalid data filtering (skips bad entries with warnings)
- Type-safe return values
- Simplified error handling

#### AutotuneService
Located in `services/autotune_service.py`

**Purpose**: User-friendly wrapper around AutotuneClient with validation

**Key Methods**:
- `run_analysis(profile, historical_data, profile_name, days)`: Run autotune and return validated recommendations
- `apply_recommendations(profile, recommendations)`: Apply autotune recommendations to a profile

**Features**:
- Automatic Pydantic validation
- Model conversion (Pydantic ↔ dict)
- Time format conversion (HH:MM:SS → HH:MM)
- Non-destructive profile updates (returns copy)
- Type-safe operations

## Usage Examples

### Loading a Profile

```python
from app.services.nightscout_service import NightscoutService

service = NightscoutService("https://mysite.herokuapp.com", "api-secret")

# Load complete profile document
profile = service.get_profile()
print(f"Default profile: {profile.defaultProfile}")

# Load specific profile from store
profile_store = service.get_profile_store("Default")
print(f"Current basal rate: {profile_store.basal[0].value} U/hr")
```

### Loading Historical Data

```python
from app.services.nightscout_service import NightscoutService

service = NightscoutService("https://mysite.herokuapp.com", "api-secret")

# Load 7 days of data
data = service.get_historical_data(days=7)
print(f"Loaded {len(data.entries)} entries")
print(f"Loaded {len(data.treatments)} treatments")

# Access validated data
for entry in data.entries:
    print(f"BG: {entry.sgv} mg/dL at {entry.dateString}")
```

### Running Autotune Analysis

```python
from app.services.nightscout_service import NightscoutService
from app.services.autotune_service import AutotuneService

# Load data from Nightscout
ns_service = NightscoutService("https://mysite.herokuapp.com", "api-secret")
profile_store = ns_service.get_profile_store("Default")
historical_data = ns_service.get_historical_data(days=7)

# Run autotune
at_service = AutotuneService()
recommendations = at_service.run_analysis(
    profile_store, 
    historical_data, 
    "Default", 
    days=7
)

print(f"Recommended carb ratio: {recommendations.result.carb_ratio} g/U")
print(f"Recommended ISF: {recommendations.result.sens} mg/dL/U")
```

### Applying Recommendations

```python
from app.services.autotune_service import AutotuneService
from app.services.nightscout_service import NightscoutService

# After running autotune analysis...
at_service = AutotuneService()

# Apply recommendations to profile (returns new profile)
updated_profile = at_service.apply_recommendations(profile_store, recommendations)

# Sync back to Nightscout
ns_service = NightscoutService("https://mysite.herokuapp.com", "api-secret")
ns_service.sync_profile(updated_profile, "Default")
```

## Testing

Unit tests are located in `tests/unit/`:
- `test_nightscout_client.py`: Tests for NightscoutClient
- `test_autotune_client.py`: Tests for AutotuneClient
- `test_nightscout_service.py`: Tests for NightscoutService
- `test_autotune_service.py`: Tests for AutotuneService

Run tests:
```bash
pytest tests/unit/
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html tests/unit/
```

## Design Principles

### Separation of Concerns
- **Clients**: Handle raw API/CLI interactions
- **Models**: Enforce data validation and type safety
- **Services**: Provide user-friendly, validated interfaces

### Type Safety
- All functions use type hints
- Pydantic models ensure runtime validation
- IDEs can provide autocomplete and type checking

### Error Handling
- Clients raise exceptions for API/CLI errors
- Services validate data and skip invalid entries
- All errors are logged with context

### Security
- HTTPS-only connections
- Hashed API secrets
- No secrets in logs
- Input validation to prevent injection

## Dependencies

- `requests`: HTTP client for Nightscout API
- `pydantic`: Data validation and models
- `prefect`: Workflow orchestration (for flows/tasks)

## Next Steps

This implementation provides the foundation for:
1. **Prefect Flows**: Create flows in `app/flows/` using these services
2. **Streamlit UI**: Build UI in `streamlit_app/` using these services
3. **Integration Tests**: Test end-to-end workflows with real/test Nightscout instances
4. **Configuration**: Add Pydantic Settings for environment-based configuration
