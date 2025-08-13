"""
Auth Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "AUTH_E001": {
        "code": "AUTH_E001",
        "message": "Authentication failed for user: {username}",
        "level": "ERROR",
        "description": "User login attempt failed due to invalid credentials"
    },
    "AUTH_E002": {
        "code": "AUTH_E002",
        "message": "Token validation failed: {token_type}",
        "level": "ERROR",
        "description": "JWT token validation or verification failed"
    },
    "AUTH_E003": {
        "code": "AUTH_E003",
        "message": "User registration failed: {error_details}",
        "level": "ERROR",
        "description": "New user registration process encountered an error"
    },
    "AUTH_E004": {
        "code": "AUTH_E004",
        "message": "Password reset failed for user: {user_id}",
        "level": "ERROR",
        "description": "Password reset operation failed"
    },
    "AUTH_E005": {
        "code": "AUTH_E005",
        "message": "Database connection failed: {error_details}",
        "level": "ERROR",
        "description": "Failed to establish connection to authentication database"
    },
    "AUTH_E006": {
        "code": "AUTH_E006",
        "message": "Permission denied for user {user_id} accessing {resource}",
        "level": "ERROR",
        "description": "User lacks required permissions for requested resource"
    },
    "AUTH_E007": {
        "code": "AUTH_E007",
        "message": "Session expired for user: {user_id}",
        "level": "ERROR",
        "description": "User session has expired and requires re-authentication"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "AUTH_I001": {
        "code": "AUTH_I001",
        "message": "User authenticated successfully: {user_id}",
        "level": "INFO",
        "description": "User login completed successfully"
    },
    "AUTH_I002": {
        "code": "AUTH_I002",
        "message": "New user registered: {user_id}",
        "level": "INFO",
        "description": "New user account created successfully"
    },
    "AUTH_I003": {
        "code": "AUTH_I003",
        "message": "User logged out: {user_id}",
        "level": "INFO",
        "description": "User session terminated successfully"
    },
    "AUTH_I004": {
        "code": "AUTH_I004",
        "message": "Password changed for user: {user_id}",
        "level": "INFO",
        "description": "User password updated successfully"
    },
    "AUTH_I005": {
        "code": "AUTH_I005",
        "message": "Token refreshed for user: {user_id}",
        "level": "INFO",
        "description": "JWT token successfully refreshed"
    },
    "AUTH_I006": {
        "code": "AUTH_I006",
        "message": "User profile updated: {user_id}",
        "level": "INFO",
        "description": "User profile information updated successfully"
    },
    "AUTH_I007": {
        "code": "AUTH_I007",
        "message": "Auth service started successfully on port {port}",
        "level": "INFO",
        "description": "Authentication service initialization completed"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "AUTH_D001": {
        "code": "AUTH_D001",
        "message": "Processing login request for username: {username}",
        "level": "DEBUG",
        "description": "Login request processing started"
    },
    "AUTH_D002": {
        "code": "AUTH_D002",
        "message": "Token payload: {token_payload}",
        "level": "DEBUG",
        "description": "JWT token payload details for debugging"
    },
    "AUTH_D003": {
        "code": "AUTH_D003",
        "message": "Password validation for user: {user_id}",
        "level": "DEBUG",
        "description": "Password validation process details"
    },
    "AUTH_D004": {
        "code": "AUTH_D004",
        "message": "Database query executed: {query_type} in {execution_time}ms",
        "level": "DEBUG",
        "description": "Database operation performance details"
    },
    "AUTH_D005": {
        "code": "AUTH_D005",
        "message": "Permission check for user {user_id} on resource {resource}",
        "level": "DEBUG",
        "description": "Authorization permission validation details"
    },
    "AUTH_D006": {
        "code": "AUTH_D006",
        "message": "Session data: {session_info}",
        "level": "DEBUG",
        "description": "User session information for debugging"
    },
    "AUTH_D007": {
        "code": "AUTH_D007",
        "message": "OAuth flow step: {oauth_step} for provider {provider}",
        "level": "DEBUG",
        "description": "OAuth authentication flow progress"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "AUTH_W001": {
        "code": "AUTH_W001",
        "message": "Multiple failed login attempts for user: {username}",
        "level": "WARNING",
        "description": "Potential brute force attack detected"
    },
    "AUTH_W002": {
        "code": "AUTH_W002",
        "message": "Token expires soon for user: {user_id}",
        "level": "WARNING",
        "description": "JWT token approaching expiration time"
    },
    "AUTH_W003": {
        "code": "AUTH_W003",
        "message": "Weak password attempted for user: {user_id}",
        "level": "WARNING",
        "description": "User attempted to set weak password"
    },
    "AUTH_W004": {
        "code": "AUTH_W004",
        "message": "Suspicious login from new location: {location} for user {user_id}",
        "level": "WARNING",
        "description": "Login from unusual geographic location"
    },
    "AUTH_W005": {
        "code": "AUTH_W005",
        "message": "High database response time: {response_time}ms",
        "level": "WARNING",
        "description": "Database performance degradation detected"
    },
    "AUTH_W006": {
        "code": "AUTH_W006",
        "message": "Rate limit approaching for IP: {ip_address}",
        "level": "WARNING",
        "description": "Client approaching authentication rate limits"
    },
    "AUTH_W007": {
        "code": "AUTH_W007",
        "message": "Inactive user account accessed: {user_id}",
        "level": "WARNING",
        "description": "Login attempt for dormant user account"
    }
}

# Combined logging messages for easy access
LOGGING_MESSAGES = {
    **ERROR_MESSAGES,
    **INFO_MESSAGES,
    **DEBUG_MESSAGES,
    **WARNING_MESSAGES
}