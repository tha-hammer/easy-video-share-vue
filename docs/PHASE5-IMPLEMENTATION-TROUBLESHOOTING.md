```

## Example Scenarios

1. **Small file (50MB) + Regular user**: Uses Celery
2. **Large file (200MB) + Any user**: Uses Lambda
3. **Small file (50MB) + Lambda user**: Uses Lambda
4. **Any file + Lambda disabled**: Uses Celery
5. **Lambda fails**: Falls back to Celery

</lambda routing>

The lambda routing does not appear to be operational. A 300MB file was just processed via Celery. The Lambda function was dormant.

Review the code attached and the summary document.
```
