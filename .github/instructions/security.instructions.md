<!-- Based on: https://github.com/github/awesome-copilot/blob/main/instructions/security-and-owasp.instructions.md -->
---
applyTo: '*'
description: 'Security best practices and OWASP guidelines for autotune-app'
---

# Security Best Practices

## Overview

Security is paramount when working with medical data and personal health information. This project handles sensitive diabetes management data from Nightscout, so we must follow strict security practices.

## General Security Principles

- **Never commit secrets** to version control (API keys, passwords, tokens)
- **Validate all inputs** from external sources (Nightscout API, user inputs)
- **Use HTTPS** for all external API communications
- **Log security events** but never log sensitive data
- **Fail securely** - default to denying access, not granting it
- **Keep dependencies updated** and scan for vulnerabilities regularly

## Secrets Management

### Environment Variables
- Store all secrets in environment variables
- Never hardcode API keys, passwords, or connection strings
- Use `.env` files for local development (add to .gitignore)
- Document required environment variables in README
- Validate that required secrets are present on startup
- Read env with pydantic-settings

### Secret Rotation
- Support secret rotation without code changes
- Don't log or display secrets in error messages
- Clear secrets from memory when no longer needed
- Use secret management services in production (AWS Secrets Manager, Azure Key Vault)

## Input Validation

### API Responses
- Validate all data received from Nightscout API
- Check data types, ranges, and formats
- Handle missing or malformed data gracefully
- Don't trust external data implicitly

Example:
```python
from typing import Dict, Any, List
from pydantic import BaseModel, validator, ValidationError
import logging

logger = logging.getLogger(__name__)


class NightscoutEntry(BaseModel):
    """Validated Nightscout glucose entry."""
    sgv: int
    date: int
    type: str
    
    @validator('sgv')
    def validate_sgv(cls, v):
        """Validate glucose value is in reasonable range."""
        if not 20 <= v <= 600:
            raise ValueError(f"Invalid glucose value: {v}")
        return v
    
    @validator('date')
    def validate_date(cls, v):
        """Validate timestamp is positive."""
        if v <= 0:
            raise ValueError(f"Invalid timestamp: {v}")
        return v


def validate_nightscout_data(data: Dict[str, Any]) -> List[NightscoutEntry]:
    """
    Validate Nightscout data using pydantic models.
    
    Args:
        data: Raw data from Nightscout API
        
    Returns:
        List of validated entries
        
    Raises:
        ValidationError: If data doesn't match expected format
    """
    try:
        entries = [NightscoutEntry(**entry) for entry in data.get('entries', [])]
        return entries
    except ValidationError as e:
        logger.error(f"Invalid Nightscout data: {e}")
        raise
```

### User Inputs
- Validate all user inputs from Streamlit UI
- Sanitize inputs before using in commands or queries
- Use allowlists for expected values when possible
- Reject unexpected or malicious inputs

## API Security

### Authentication
- Always use API secrets for Nightscout authentication
- Use secure headers for API authentication
- Don't include secrets in URL parameters
- Implement token refresh for long-running processes

Example:
```python
import hashlib
import requests
from typing import Dict, Any


def get_auth_headers(api_secret: str) -> Dict[str, str]:
    """
    Generate secure authentication headers for Nightscout.
    
    Args:
        api_secret: Nightscout API secret
        
    Returns:
        Dict containing authentication headers
    """
    # Hash the API secret for authentication
    api_secret_hash = hashlib.sha1(api_secret.encode()).hexdigest()
    
    return {
        'API-SECRET': api_secret_hash,
        'Content-Type': 'application/json'
    }


def fetch_with_auth(url: str, api_secret: str) -> Dict[str, Any]:
    """Fetch data with secure authentication."""
    headers = get_auth_headers(api_secret)
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
```

### HTTPS Only
- Always use HTTPS for external API calls
- Reject HTTP URLs in configuration
- Verify SSL certificates (don't disable verification)
- Use certificate pinning for critical connections if needed

Example:
```python
def validate_url(url: str) -> str:
    """
    Validate URL is HTTPS.
    
    Args:
        url: URL to validate
        
    Returns:
        str: Validated URL
        
    Raises:
        ValueError: If URL is not HTTPS
    """
    if not url.startswith('https://'):
        raise ValueError(f"URL must use HTTPS: {url}")
    return url
```

### Rate Limiting
- Implement rate limiting for API calls
- Use exponential backoff for retries
- Respect API rate limits from Nightscout
- Cache responses to minimize API calls

## Data Protection

### Sensitive Data Handling
- Treat all health data as sensitive
- Don't log glucose values, insulin doses, or personal data
- Encrypt data at rest if storing locally
- Use secure temporary files if needed

Example:
```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def log_api_call(url: str, status_code: int, data: Dict[str, Any]) -> None:
    """
    Log API call without exposing sensitive data.
    
    Args:
        url: API endpoint (without query parameters)
        status_code: HTTP status code
        data: Response data (will not be logged)
    """
    # GOOD: Log only non-sensitive information
    logger.info(
        f"API call to {url} completed with status {status_code}, "
        f"returned {len(data)} items"
    )
    
    # BAD: Never log sensitive data
    # logger.info(f"API response: {data}")  # NEVER DO THIS
```

### Data Minimization
- Only request data you actually need
- Don't store data longer than necessary
- Delete temporary files after processing
- Use data retention policies

## Dependency Security

### Vulnerability Scanning
- Regularly scan dependencies for known vulnerabilities
- Use `pip-audit` or `safety` to check Python packages
- Update dependencies to patch security issues
- Pin dependency versions in requirements.txt

Example commands:
```bash
# Scan for vulnerabilities
pip-audit

# Or use safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade <package>
```

### Dependency Management
- Use virtual environments to isolate dependencies
- Review dependencies before adding to project
- Prefer well-maintained, popular packages
- Remove unused dependencies

## Docker Security

### Container Best Practices
- Run containers as non-root user
- Use minimal base images (alpine, slim)
- Don't include secrets in Docker images
- Scan images for vulnerabilities
- Keep base images updated

Example Dockerfile:
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Run application
CMD ["python", "-m", "autotune_app"]
```

## Error Handling

### Secure Error Messages
- Don't expose system details in error messages
- Log detailed errors internally
- Show generic error messages to users
- Never display stack traces to users in production

Example:
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def fetch_profile_safely(url: str, api_secret: str) -> Optional[dict]:
    """
    Fetch profile with secure error handling.
    
    Args:
        url: Nightscout URL
        api_secret: API secret
        
    Returns:
        Profile data or None if error occurs
    """
    try:
        # Attempt to fetch profile
        profile = fetch_profile(url, api_secret)
        return profile
    except requests.HTTPError as e:
        # Log detailed error internally
        logger.error(
            f"Failed to fetch profile from {url}: {e.response.status_code}",
            exc_info=True
        )
        # Return generic error to user
        return None
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error fetching profile: {type(e).__name__}", exc_info=True)
        # Don't expose error details
        return None
```

## Logging Security

### What to Log
- ✅ Authentication attempts (success and failure)
- ✅ API calls (endpoint, status code, duration)
- ✅ Configuration changes
- ✅ Error conditions and exceptions
- ✅ Security-relevant events

### What NOT to Log
- ❌ API secrets or passwords
- ❌ Personal health data (glucose values, insulin doses)
- ❌ User identifiable information
- ❌ Full API responses with sensitive data
- ❌ Detailed system information that could aid attackers

Example:
```python
# GOOD: Log without sensitive data
logger.info(f"Successfully fetched profile for user {user_id[:8]}...")
logger.error(f"Authentication failed for request from {ip_address}")

# BAD: Logging sensitive data
# logger.info(f"API secret: {api_secret}")  # NEVER
# logger.debug(f"Glucose value: {sgv}")  # AVOID
```

## Prefect Security

### Flow Security
- Don't store secrets in flow parameters
- Use Prefect Secrets for sensitive configuration
- Secure Prefect API with authentication
- Use RBAC in Prefect Cloud if available

### Task Security
- Validate inputs in task parameters
- Don't log sensitive task results
- Use secure communication between tasks
- Implement task-level error handling

## OWASP Top 10 Considerations

### A01: Broken Access Control
- Validate that users can only access their own Nightscout data
- Implement proper authorization checks
- Don't rely on client-side access control

### A02: Cryptographic Failures
- Use HTTPS for all API communications
- Hash API secrets before sending
- Use strong encryption for data at rest
- Don't implement custom cryptography

### A03: Injection
- Use parameterized queries if using databases
- Validate and sanitize all inputs
- Don't construct commands from user input
- Use allowlists for expected values

### A05: Security Misconfiguration
- Disable debug mode in production
- Remove unnecessary features and endpoints
- Use secure defaults for all configuration
- Keep all components updated

### A06: Vulnerable Components
- Regularly update dependencies
- Scan for known vulnerabilities
- Remove unused dependencies
- Monitor security advisories

### A09: Security Logging and Monitoring
- Log security events
- Monitor for suspicious activity
- Set up alerts for security issues
- Review logs regularly

### A10: Server-Side Request Forgery (SSRF)
- Validate Nightscout URLs
- Use allowlists for external URLs
- Don't follow redirects blindly
- Implement timeouts for external requests

## Security Checklist

Before deploying or releasing code:

- [ ] No secrets committed to version control
- [ ] All external inputs validated
- [ ] HTTPS used for all external communications
- [ ] Dependencies scanned for vulnerabilities
- [ ] Error messages don't expose sensitive information
- [ ] Logging doesn't include sensitive data
- [ ] Containers run as non-root user
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Authentication and authorization tested
- [ ] Security documentation updated

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Nightscout Security Documentation](https://nightscout.github.io/nightscout/security/)
