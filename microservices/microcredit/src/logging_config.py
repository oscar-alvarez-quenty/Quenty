"""
Microcredit Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "MC_E001": {
        "code": "MC_E001",
        "message": "Credit assessment failed: {customer_id} - {error_details}",
        "level": "ERROR",
        "description": "Customer credit evaluation process failed"
    },
    "MC_E002": {
        "code": "MC_E002",
        "message": "Loan application processing failed: {application_id}",
        "level": "ERROR",
        "description": "Microcredit loan application processing error"
    },
    "MC_E003": {
        "code": "MC_E003",
        "message": "Payment processing failed: {payment_id} for loan {loan_id}",
        "level": "ERROR",
        "description": "Loan payment processing encountered an error"
    },
    "MC_E004": {
        "code": "MC_E004",
        "message": "Credit score calculation failed: {customer_id}",
        "level": "ERROR",
        "description": "Credit scoring algorithm error"
    },
    "MC_E005": {
        "code": "MC_E005",
        "message": "Loan disbursement failed: {loan_id}",
        "level": "ERROR",
        "description": "Loan amount disbursement process failed"
    },
    "MC_E006": {
        "code": "MC_E006",
        "message": "Interest calculation error: {loan_id}",
        "level": "ERROR",
        "description": "Loan interest calculation process failed"
    },
    "MC_E007": {
        "code": "MC_E007",
        "message": "Loan default processing failed: {loan_id}",
        "level": "ERROR",
        "description": "Loan default handling process encountered error"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "MC_I001": {
        "code": "MC_I001",
        "message": "Loan application approved: {application_id} amount {loan_amount}",
        "level": "INFO",
        "description": "Microcredit loan application approved successfully"
    },
    "MC_I002": {
        "code": "MC_I002",
        "message": "Loan disbursed: {loan_id} amount {amount} to customer {customer_id}",
        "level": "INFO",
        "description": "Loan amount successfully disbursed"
    },
    "MC_I003": {
        "code": "MC_I003",
        "message": "Payment received: {payment_id} amount {amount} for loan {loan_id}",
        "level": "INFO",
        "description": "Loan payment received and processed"
    },
    "MC_I004": {
        "code": "MC_I004",
        "message": "Loan repaid in full: {loan_id}",
        "level": "INFO",
        "description": "Loan completely repaid by customer"
    },
    "MC_I005": {
        "code": "MC_I005",
        "message": "Credit limit updated: {customer_id} new limit {credit_limit}",
        "level": "INFO",
        "description": "Customer credit limit adjusted"
    },
    "MC_I006": {
        "code": "MC_I006",
        "message": "Microcredit service started successfully on port {port}",
        "level": "INFO",
        "description": "Microcredit service initialization completed"
    },
    "MC_I007": {
        "code": "MC_I007",
        "message": "Credit assessment completed: {customer_id} score {credit_score}",
        "level": "INFO",
        "description": "Customer credit assessment successfully completed"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "MC_D001": {
        "code": "MC_D001",
        "message": "Processing credit request: {request_type} for customer {customer_id}",
        "level": "DEBUG",
        "description": "Credit request processing details"
    },
    "MC_D002": {
        "code": "MC_D002",
        "message": "Credit score factors: {scoring_factors}",
        "level": "DEBUG",
        "description": "Credit scoring calculation factors"
    },
    "MC_D003": {
        "code": "MC_D003",
        "message": "Interest calculation: principal {principal} rate {rate}% term {term} months",
        "level": "DEBUG",
        "description": "Loan interest calculation parameters"
    },
    "MC_D004": {
        "code": "MC_D004",
        "message": "Payment schedule generated: {loan_id} {installments_count} installments",
        "level": "DEBUG",
        "description": "Loan repayment schedule generation details"
    },
    "MC_D005": {
        "code": "MC_D005",
        "message": "Risk assessment: {customer_id} risk level {risk_level}",
        "level": "DEBUG",
        "description": "Customer risk assessment result"
    },
    "MC_D006": {
        "code": "MC_D006",
        "message": "Database query: {query_type} for loan {loan_id} in {execution_time}ms",
        "level": "DEBUG",
        "description": "Microcredit database operation performance"
    },
    "MC_D007": {
        "code": "MC_D007",
        "message": "Collateral evaluation: {collateral_type} value {collateral_value}",
        "level": "DEBUG",
        "description": "Loan collateral assessment details"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "MC_W001": {
        "code": "MC_W001",
        "message": "Late payment detected: {loan_id} overdue by {days_overdue} days",
        "level": "WARNING",
        "description": "Loan payment is overdue"
    },
    "MC_W002": {
        "code": "MC_W002",
        "message": "High risk customer: {customer_id} risk score {risk_score}",
        "level": "WARNING",
        "description": "Customer has high credit risk profile"
    },
    "MC_W003": {
        "code": "MC_W003",
        "message": "Credit utilization high: {customer_id} using {utilization_percentage}% of limit",
        "level": "WARNING",
        "description": "Customer approaching credit limit"
    },
    "MC_W004": {
        "code": "MC_W004",
        "message": "Multiple loan applications: {customer_id} ({applications_count} in {time_period})",
        "level": "WARNING",
        "description": "Customer submitting multiple loan applications"
    },
    "MC_W005": {
        "code": "MC_W005",
        "message": "Interest rate volatility: {rate_change_percentage}% change detected",
        "level": "WARNING",
        "description": "Significant interest rate fluctuation"
    },
    "MC_W006": {
        "code": "MC_W006",
        "message": "Loan default risk: {loan_id} probability {default_probability}%",
        "level": "WARNING",
        "description": "Loan showing high probability of default"
    },
    "MC_W007": {
        "code": "MC_W007",
        "message": "Microcredit service memory usage high: {memory_percentage}%",
        "level": "WARNING",
        "description": "Service memory usage approaching critical levels"
    }
}

# Combined logging messages for easy access
LOGGING_MESSAGES = {
    **ERROR_MESSAGES,
    **INFO_MESSAGES,
    **DEBUG_MESSAGES,
    **WARNING_MESSAGES
}