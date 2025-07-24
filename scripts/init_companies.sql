-- SQL script to initialize companies in the auth database
-- This should be run after the auth-service database is ready

-- Connect to the auth_db database
\c auth_db;

-- Insert initial companies
INSERT INTO companies (
    company_id,
    name,
    business_name,
    document_type,
    document_number,
    industry,
    company_size,
    subscription_plan,
    is_active,
    is_verified,
    settings,
    created_at,
    updated_at
) VALUES 
(
    'COMP-TECH0001',
    'Tech Solutions Inc',
    'Tech Solutions Incorporated',
    'NIT',
    '900123456-7',
    'technology',
    'medium',
    'enterprise',
    true,
    true,
    '{"notifications_enabled": true, "auto_approve_orders": false, "default_currency": "COP"}',
    NOW(),
    NOW()
),
(
    'COMP-GLOB0002',
    'Global Logistics Co',
    'Global Logistics Company',
    'NIT',
    '900789012-3',
    'logistics',
    'large',
    'pro',
    true,
    true,
    '{"notifications_enabled": true, "auto_approve_orders": true, "default_currency": "USD"}',
    NOW(),
    NOW()
),
(
    'COMP-LOCA0003',
    'Local Store',
    'Local Store SAS',
    'NIT',
    '900345678-9',
    'retail',
    'small',
    'basic',
    true,
    true,
    '{"notifications_enabled": true, "auto_approve_orders": false, "default_currency": "COP"}',
    NOW(),
    NOW()
)
ON CONFLICT (company_id) DO NOTHING;