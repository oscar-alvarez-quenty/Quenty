# Frontend Integration Examples - Auth Requirements

This document provides comprehensive examples for integrating the new authentication features into the frontend application.

## Table of Contents

1. [Public User Registration](#1-public-user-registration)
2. [Password Reset Flow](#2-password-reset-flow)
3. [Form Validation](#3-form-validation)
4. [Error Handling](#4-error-handling)
5. [React Component Examples](#5-react-component-examples)
6. [API Client Examples](#6-api-client-examples)

---

## 1. Public User Registration

### 1.1 Registration for Individual (Natural) Users

#### API Endpoint
```
POST /api/v1/auth/register
Content-Type: application/json
```

#### Request Body Example (Natural User)
```json
{
  "user_type": "natural",
  "email": "juan.perez@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "document_type_code": "cedula",
  "document_number": "1234567890",
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone": "+573001234567",
  "terms_accepted": true,
  "privacy_policy_accepted": true,
  "marketing_consent": false
}
```

#### Success Response (201 Created)
```json
{
  "message": "Registration successful",
  "user_id": 123,
  "unique_id": "USER-ABC12345",
  "email": "juan.perez@example.com",
  "user_type": "natural",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 1.2 Registration for Company (Juridica) Users

#### Request Body Example (Juridica User)
```json
{
  "user_type": "juridica",
  "email": "admin@miempresa.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "document_type_code": "nit",
  "document_number": "9001234567",
  "first_name": "Carlos",
  "last_name": "Empresario",
  "phone": "+573009876543",
  "terms_accepted": true,
  "privacy_policy_accepted": true,
  "marketing_consent": true,
  "company_data": {
    "name": "Mi Empresa S.A.S",
    "nit": "9001234567"
  }
}
```

#### Success Response (201 Created)
```json
{
  "message": "Registration successful",
  "user_id": 124,
  "unique_id": "USER-XYZ98765",
  "email": "admin@miempresa.com",
  "user_type": "juridica",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 1.3 Error Responses

#### Email Already Registered (400 Bad Request)
```json
{
  "detail": "Email already registered"
}
```

#### Document Number Already Registered (400 Bad Request)
```json
{
  "detail": "Document number already registered"
}
```

#### Company NIT Already Registered (400 Bad Request)
```json
{
  "detail": "Company NIT already registered"
}
```

#### Validation Error (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "loc": ["body", "terms_accepted"],
      "msg": "Terms and conditions must be accepted",
      "type": "value_error"
    }
  ]
}
```

---

## 2. Password Reset Flow

### 2.1 Step 1: Request Password Reset

#### API Endpoint
```
POST /api/v1/auth/password-reset/request
Content-Type: application/json
```

#### Request Body
```json
{
  "email": "juan.perez@example.com"
}
```

#### Success Response (200 OK)
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

**Note:** The API always returns success to prevent email enumeration attacks. The user will receive an email if the account exists.

#### Email Example
```
Subject: Recuperación de Contraseña - Quenty

Hola Juan,

Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Quenty.

Para crear una nueva contraseña, haz clic en el siguiente botón:

[Restablecer Contraseña] (links to: https://app.quenty.com/auth/reset-password?token=abc123xyz...)

Este enlace expirará en 1 hora.

Si no solicitaste restablecer tu contraseña, puedes ignorar este correo de forma segura.
```

### 2.2 Step 2: Confirm Password Reset

#### API Endpoint
```
POST /api/v1/auth/password-reset/confirm
Content-Type: application/json
```

#### Request Body
```json
{
  "token": "abc123xyz...",
  "new_password": "NewSecurePass456!",
  "new_password_confirm": "NewSecurePass456!"
}
```

#### Success Response (200 OK)
```json
{
  "message": "Password reset successful. Please log in with your new password."
}
```

#### Error Response - Invalid Token (400 Bad Request)
```json
{
  "detail": "Invalid or expired reset token"
}
```

---

## 3. Form Validation

### 3.1 Client-Side Validation Rules

#### Email
- **Required**: Yes
- **Format**: Valid email format
- **Example**: `usuario@dominio.com`

#### Password
- **Required**: Yes
- **Min Length**: 8 characters
- **Max Length**: 100 characters
- **Recommended**: Include uppercase, lowercase, numbers, and special characters
- **Example**: `SecurePass123!`

#### Document Number
- **Required**: Yes
- **Min Length**: 5 characters
- **Max Length**: 100 characters
- **Format**: Alphanumeric (varies by document type)

#### NIT (for juridica)
- **Required**: Yes (only for juridica users)
- **Min Length**: 9 digits
- **Max Length**: 20 characters
- **Format**: Numeric only
- **Example**: `9001234567`

#### Terms & Privacy Policy
- **Required**: Yes
- **Type**: Boolean (checkbox)
- **Must be**: `true` to proceed

#### Marketing Consent
- **Required**: No
- **Type**: Boolean (checkbox)
- **Default**: `false`

### 3.2 JavaScript Validation Example

```javascript
function validateRegistrationForm(formData) {
  const errors = {};

  // Email validation
  if (!formData.email) {
    errors.email = 'Email es requerido';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errors.email = 'Formato de email inválido';
  }

  // Password validation
  if (!formData.password) {
    errors.password = 'Contraseña es requerida';
  } else if (formData.password.length < 8) {
    errors.password = 'La contraseña debe tener al menos 8 caracteres';
  }

  // Password confirmation
  if (formData.password !== formData.password_confirm) {
    errors.password_confirm = 'Las contraseñas no coinciden';
  }

  // Document number validation
  if (!formData.document_number) {
    errors.document_number = 'Número de documento es requerido';
  } else if (formData.document_number.length < 5) {
    errors.document_number = 'Número de documento inválido';
  }

  // For natural users, validate names
  if (formData.user_type === 'natural') {
    if (!formData.first_name) {
      errors.first_name = 'Nombre es requerido';
    }
    if (!formData.last_name) {
      errors.last_name = 'Apellido es requerido';
    }
  }

  // For juridica users, validate company data
  if (formData.user_type === 'juridica') {
    if (!formData.company_data?.name) {
      errors.company_name = 'Nombre de empresa es requerido';
    }
    if (!formData.company_data?.nit) {
      errors.company_nit = 'NIT es requerido';
    } else if (!/^\d{9,}$/.test(formData.company_data.nit.replace(/\D/g, ''))) {
      errors.company_nit = 'NIT debe tener al menos 9 dígitos';
    }
  }

  // Terms validation
  if (!formData.terms_accepted) {
    errors.terms_accepted = 'Debes aceptar los términos y condiciones';
  }

  // Privacy policy validation
  if (!formData.privacy_policy_accepted) {
    errors.privacy_policy_accepted = 'Debes aceptar la política de privacidad';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}
```

---

## 4. Error Handling

### 4.1 HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 200 | Success | Password reset request accepted |
| 201 | Created | Registration successful |
| 400 | Bad Request | Email/document already exists, validation failed |
| 401 | Unauthorized | Invalid credentials (login) |
| 422 | Unprocessable Entity | Schema validation error |
| 500 | Internal Server Error | Server-side error |

### 4.2 Error Handling Example

```javascript
async function registerUser(registrationData) {
  try {
    const response = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(registrationData)
    });

    if (!response.ok) {
      const errorData = await response.json();

      // Handle specific error cases
      if (response.status === 400) {
        // Business logic errors
        throw new Error(errorData.detail);
      } else if (response.status === 422) {
        // Validation errors
        const validationErrors = {};
        errorData.detail.forEach(err => {
          const field = err.loc[err.loc.length - 1];
          validationErrors[field] = err.msg;
        });
        throw { validationErrors };
      } else {
        throw new Error('Error en el registro. Por favor intenta de nuevo.');
      }
    }

    const data = await response.json();

    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;

  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
}
```

---

## 5. React Component Examples

### 5.1 Natural User Registration Form

```jsx
import React, { useState } from 'react';

function NaturalUserRegistrationForm() {
  const [formData, setFormData] = useState({
    user_type: 'natural',
    email: '',
    password: '',
    password_confirm: '',
    document_type_code: 'cedula',
    document_number: '',
    first_name: '',
    last_name: '',
    phone: '',
    terms_accepted: false,
    privacy_policy_accepted: false,
    marketing_consent: false
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 422) {
          const validationErrors = {};
          errorData.detail.forEach(err => {
            const field = err.loc[err.loc.length - 1];
            validationErrors[field] = err.msg;
          });
          setErrors(validationErrors);
        } else {
          setErrors({ general: errorData.detail });
        }
        return;
      }

      const data = await response.json();

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      // Redirect to dashboard
      window.location.href = '/dashboard';

    } catch (error) {
      setErrors({ general: 'Error al registrar. Por favor intenta de nuevo.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="registration-form">
      <h2>Registro de Usuario</h2>

      {errors.general && (
        <div className="alert alert-error">{errors.general}</div>
      )}

      <div className="form-group">
        <label htmlFor="email">Email *</label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          className={errors.email ? 'error' : ''}
        />
        {errors.email && <span className="error-text">{errors.email}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="first_name">Nombre *</label>
        <input
          type="text"
          id="first_name"
          name="first_name"
          value={formData.first_name}
          onChange={handleChange}
          required
          className={errors.first_name ? 'error' : ''}
        />
        {errors.first_name && <span className="error-text">{errors.first_name}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="last_name">Apellido *</label>
        <input
          type="text"
          id="last_name"
          name="last_name"
          value={formData.last_name}
          onChange={handleChange}
          required
          className={errors.last_name ? 'error' : ''}
        />
        {errors.last_name && <span className="error-text">{errors.last_name}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="document_type_code">Tipo de Documento *</label>
        <select
          id="document_type_code"
          name="document_type_code"
          value={formData.document_type_code}
          onChange={handleChange}
          required
        >
          <option value="cedula">Cédula de Ciudadanía</option>
          <option value="cedula_extranjeria">Cédula de Extranjería</option>
          <option value="passport">Pasaporte</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="document_number">Número de Documento *</label>
        <input
          type="text"
          id="document_number"
          name="document_number"
          value={formData.document_number}
          onChange={handleChange}
          required
          className={errors.document_number ? 'error' : ''}
        />
        {errors.document_number && <span className="error-text">{errors.document_number}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="phone">Teléfono</label>
        <input
          type="tel"
          id="phone"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="+573001234567"
        />
      </div>

      <div className="form-group">
        <label htmlFor="password">Contraseña *</label>
        <input
          type="password"
          id="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          required
          minLength={8}
          className={errors.password ? 'error' : ''}
        />
        {errors.password && <span className="error-text">{errors.password}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="password_confirm">Confirmar Contraseña *</label>
        <input
          type="password"
          id="password_confirm"
          name="password_confirm"
          value={formData.password_confirm}
          onChange={handleChange}
          required
          minLength={8}
          className={errors.password_confirm ? 'error' : ''}
        />
        {errors.password_confirm && <span className="error-text">{errors.password_confirm}</span>}
      </div>

      <div className="form-group checkbox">
        <label>
          <input
            type="checkbox"
            name="terms_accepted"
            checked={formData.terms_accepted}
            onChange={handleChange}
            required
          />
          Acepto los <a href="/terms" target="_blank">términos y condiciones</a> *
        </label>
        {errors.terms_accepted && <span className="error-text">{errors.terms_accepted}</span>}
      </div>

      <div className="form-group checkbox">
        <label>
          <input
            type="checkbox"
            name="privacy_policy_accepted"
            checked={formData.privacy_policy_accepted}
            onChange={handleChange}
            required
          />
          Acepto la <a href="/privacy" target="_blank">política de privacidad</a> *
        </label>
        {errors.privacy_policy_accepted && <span className="error-text">{errors.privacy_policy_accepted}</span>}
      </div>

      <div className="form-group checkbox">
        <label>
          <input
            type="checkbox"
            name="marketing_consent"
            checked={formData.marketing_consent}
            onChange={handleChange}
          />
          Deseo recibir información sobre promociones y novedades
        </label>
      </div>

      <button type="submit" disabled={loading} className="btn-primary">
        {loading ? 'Registrando...' : 'Registrarse'}
      </button>
    </form>
  );
}

export default NaturalUserRegistrationForm;
```

### 5.2 Juridica User Registration Form

```jsx
import React, { useState } from 'react';

function JuridicaUserRegistrationForm() {
  const [formData, setFormData] = useState({
    user_type: 'juridica',
    email: '',
    password: '',
    password_confirm: '',
    document_type_code: 'nit',
    document_number: '',
    first_name: '',
    last_name: '',
    phone: '',
    terms_accepted: false,
    privacy_policy_accepted: false,
    marketing_consent: false,
    company_data: {
      name: '',
      nit: ''
    }
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    if (name.startsWith('company_')) {
      const companyField = name.replace('company_', '');
      setFormData(prev => ({
        ...prev,
        company_data: {
          ...prev.company_data,
          [companyField]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 422) {
          const validationErrors = {};
          errorData.detail.forEach(err => {
            const field = err.loc[err.loc.length - 1];
            validationErrors[field] = err.msg;
          });
          setErrors(validationErrors);
        } else {
          setErrors({ general: errorData.detail });
        }
        return;
      }

      const data = await response.json();

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      // Redirect to dashboard
      window.location.href = '/dashboard';

    } catch (error) {
      setErrors({ general: 'Error al registrar. Por favor intenta de nuevo.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="registration-form">
      <h2>Registro de Empresa</h2>

      {errors.general && (
        <div className="alert alert-error">{errors.general}</div>
      )}

      <div className="form-section">
        <h3>Datos de la Empresa</h3>

        <div className="form-group">
          <label htmlFor="company_name">Nombre de la Empresa *</label>
          <input
            type="text"
            id="company_name"
            name="company_name"
            value={formData.company_data.name}
            onChange={handleChange}
            required
            className={errors.company_name ? 'error' : ''}
          />
          {errors.company_name && <span className="error-text">{errors.company_name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="company_nit">NIT de la Empresa *</label>
          <input
            type="text"
            id="company_nit"
            name="company_nit"
            value={formData.company_data.nit}
            onChange={handleChange}
            required
            placeholder="9001234567"
            className={errors.company_nit ? 'error' : ''}
          />
          {errors.company_nit && <span className="error-text">{errors.company_nit}</span>}
        </div>
      </div>

      <div className="form-section">
        <h3>Datos del Representante Legal</h3>

        <div className="form-group">
          <label htmlFor="email">Email *</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className={errors.email ? 'error' : ''}
          />
          {errors.email && <span className="error-text">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="first_name">Nombre *</label>
          <input
            type="text"
            id="first_name"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            required
            className={errors.first_name ? 'error' : ''}
          />
          {errors.first_name && <span className="error-text">{errors.first_name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="last_name">Apellido *</label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            required
            className={errors.last_name ? 'error' : ''}
          />
          {errors.last_name && <span className="error-text">{errors.last_name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="document_number">Cédula del Representante Legal *</label>
          <input
            type="text"
            id="document_number"
            name="document_number"
            value={formData.document_number}
            onChange={handleChange}
            required
            className={errors.document_number ? 'error' : ''}
          />
          {errors.document_number && <span className="error-text">{errors.document_number}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="phone">Teléfono</label>
          <input
            type="tel"
            id="phone"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            placeholder="+573001234567"
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Contraseña *</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={8}
            className={errors.password ? 'error' : ''}
          />
          {errors.password && <span className="error-text">{errors.password}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="password_confirm">Confirmar Contraseña *</label>
          <input
            type="password"
            id="password_confirm"
            name="password_confirm"
            value={formData.password_confirm}
            onChange={handleChange}
            required
            minLength={8}
            className={errors.password_confirm ? 'error' : ''}
          />
          {errors.password_confirm && <span className="error-text">{errors.password_confirm}</span>}
        </div>
      </div>

      <div className="form-section">
        <div className="form-group checkbox">
          <label>
            <input
              type="checkbox"
              name="terms_accepted"
              checked={formData.terms_accepted}
              onChange={handleChange}
              required
            />
            Acepto los <a href="/terms" target="_blank">términos y condiciones</a> *
          </label>
          {errors.terms_accepted && <span className="error-text">{errors.terms_accepted}</span>}
        </div>

        <div className="form-group checkbox">
          <label>
            <input
              type="checkbox"
              name="privacy_policy_accepted"
              checked={formData.privacy_policy_accepted}
              onChange={handleChange}
              required
            />
            Acepto la <a href="/privacy" target="_blank">política de privacidad</a> *
          </label>
          {errors.privacy_policy_accepted && <span className="error-text">{errors.privacy_policy_accepted}</span>}
        </div>

        <div className="form-group checkbox">
          <label>
            <input
              type="checkbox"
              name="marketing_consent"
              checked={formData.marketing_consent}
              onChange={handleChange}
            />
            Deseo recibir información sobre promociones y novedades
          </label>
        </div>
      </div>

      <button type="submit" disabled={loading} className="btn-primary">
        {loading ? 'Registrando...' : 'Registrar Empresa'}
      </button>
    </form>
  );
}

export default JuridicaUserRegistrationForm;
```

### 5.3 Password Reset Request Form

```jsx
import React, { useState } from 'react';

function PasswordResetRequestForm() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/v1/auth/password-reset/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      });

      // API always returns 200 to prevent email enumeration
      setSubmitted(true);

    } catch (error) {
      setError('Error al procesar la solicitud. Por favor intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="success-message">
        <h2>Solicitud Enviada</h2>
        <p>Si existe una cuenta con el email proporcionado, recibirás un enlace para restablecer tu contraseña.</p>
        <p>Por favor revisa tu bandeja de entrada y spam.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="password-reset-form">
      <h2>Recuperar Contraseña</h2>
      <p>Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña.</p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder="tu@email.com"
        />
      </div>

      <button type="submit" disabled={loading} className="btn-primary">
        {loading ? 'Enviando...' : 'Enviar Enlace'}
      </button>

      <div className="form-footer">
        <a href="/auth/login">Volver al inicio de sesión</a>
      </div>
    </form>
  );
}

export default PasswordResetRequestForm;
```

### 5.4 Password Reset Confirmation Form

```jsx
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

function PasswordResetConfirmForm() {
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState({
    token: '',
    new_password: '',
    new_password_confirm: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setFormData(prev => ({ ...prev, token }));
    }
  }, [searchParams]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const response = await fetch('/api/v1/auth/password-reset/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 422) {
          const validationErrors = {};
          errorData.detail.forEach(err => {
            const field = err.loc[err.loc.length - 1];
            validationErrors[field] = err.msg;
          });
          setErrors(validationErrors);
        } else {
          setErrors({ general: errorData.detail });
        }
        return;
      }

      setSuccess(true);

      // Redirect to login after 3 seconds
      setTimeout(() => {
        window.location.href = '/auth/login';
      }, 3000);

    } catch (error) {
      setErrors({ general: 'Error al restablecer la contraseña. Por favor intenta de nuevo.' });
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="success-message">
        <h2>Contraseña Restablecida</h2>
        <p>Tu contraseña ha sido actualizada exitosamente.</p>
        <p>Serás redirigido al inicio de sesión en unos segundos...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="password-reset-confirm-form">
      <h2>Crear Nueva Contraseña</h2>

      {errors.general && (
        <div className="alert alert-error">{errors.general}</div>
      )}

      <div className="form-group">
        <label htmlFor="new_password">Nueva Contraseña</label>
        <input
          type="password"
          id="new_password"
          name="new_password"
          value={formData.new_password}
          onChange={handleChange}
          required
          minLength={8}
          className={errors.new_password ? 'error' : ''}
        />
        {errors.new_password && <span className="error-text">{errors.new_password}</span>}
        <small>Mínimo 8 caracteres</small>
      </div>

      <div className="form-group">
        <label htmlFor="new_password_confirm">Confirmar Nueva Contraseña</label>
        <input
          type="password"
          id="new_password_confirm"
          name="new_password_confirm"
          value={formData.new_password_confirm}
          onChange={handleChange}
          required
          minLength={8}
          className={errors.new_password_confirm ? 'error' : ''}
        />
        {errors.new_password_confirm && <span className="error-text">{errors.new_password_confirm}</span>}
      </div>

      <button type="submit" disabled={loading} className="btn-primary">
        {loading ? 'Restableciendo...' : 'Restablecer Contraseña'}
      </button>
    </form>
  );
}

export default PasswordResetConfirmForm;
```

---

## 6. API Client Examples

### 6.1 Axios Client with Interceptors

```javascript
import axios from 'axios';

// Create axios instance
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          `${process.env.REACT_APP_API_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/auth/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API functions
export const authAPI = {
  // Register natural user
  registerNatural: async (userData) => {
    const response = await apiClient.post('/api/v1/auth/register', {
      user_type: 'natural',
      ...userData
    });
    return response.data;
  },

  // Register juridica user
  registerJuridica: async (userData) => {
    const response = await apiClient.post('/api/v1/auth/register', {
      user_type: 'juridica',
      ...userData
    });
    return response.data;
  },

  // Login
  login: async (usernameOrEmail, password, rememberMe = false) => {
    const response = await apiClient.post('/api/v1/auth/login', {
      username_or_email: usernameOrEmail,
      password,
      remember_me: rememberMe
    });
    return response.data;
  },

  // Request password reset
  requestPasswordReset: async (email) => {
    const response = await apiClient.post('/api/v1/auth/password-reset/request', {
      email
    });
    return response.data;
  },

  // Confirm password reset
  confirmPasswordReset: async (token, newPassword, newPasswordConfirm) => {
    const response = await apiClient.post('/api/v1/auth/password-reset/confirm', {
      token,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm
    });
    return response.data;
  },

  // Logout
  logout: async () => {
    const response = await apiClient.post('/api/v1/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return response.data;
  },

  // Get current user profile
  getProfile: async () => {
    const response = await apiClient.get('/api/v1/profile');
    return response.data;
  }
};

export default apiClient;
```

### 6.2 Usage Examples

```javascript
// Example 1: Register natural user
import { authAPI } from './apiClient';

async function handleNaturalRegistration(formData) {
  try {
    const response = await authAPI.registerNatural({
      email: formData.email,
      password: formData.password,
      password_confirm: formData.passwordConfirm,
      document_type_code: formData.documentType,
      document_number: formData.documentNumber,
      first_name: formData.firstName,
      last_name: formData.lastName,
      phone: formData.phone,
      terms_accepted: formData.termsAccepted,
      privacy_policy_accepted: formData.privacyPolicyAccepted,
      marketing_consent: formData.marketingConsent
    });

    // Store tokens
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);

    return response;
  } catch (error) {
    console.error('Registration failed:', error);
    throw error;
  }
}

// Example 2: Register juridica user
async function handleJuridicaRegistration(formData) {
  try {
    const response = await authAPI.registerJuridica({
      email: formData.email,
      password: formData.password,
      password_confirm: formData.passwordConfirm,
      document_type_code: 'nit',
      document_number: formData.nit,
      first_name: formData.firstName,
      last_name: formData.lastName,
      phone: formData.phone,
      terms_accepted: formData.termsAccepted,
      privacy_policy_accepted: formData.privacyPolicyAccepted,
      marketing_consent: formData.marketingConsent,
      company_data: {
        name: formData.companyName,
        nit: formData.nit
      }
    });

    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);

    return response;
  } catch (error) {
    console.error('Registration failed:', error);
    throw error;
  }
}

// Example 3: Password reset flow
async function handlePasswordResetRequest(email) {
  try {
    await authAPI.requestPasswordReset(email);
    alert('Si el email existe, recibirás un enlace de recuperación');
  } catch (error) {
    console.error('Password reset request failed:', error);
  }
}

async function handlePasswordResetConfirm(token, newPassword, newPasswordConfirm) {
  try {
    await authAPI.confirmPasswordReset(token, newPassword, newPasswordConfirm);
    alert('Contraseña restablecida exitosamente');
    window.location.href = '/auth/login';
  } catch (error) {
    console.error('Password reset confirm failed:', error);
    throw error;
  }
}
```

---

## Summary

This document provides complete integration examples for:

1. **Public User Registration**: Both natural (individual) and juridica (company) registration flows
2. **Password Reset**: Complete two-step password recovery process
3. **Form Validation**: Client-side validation rules and examples
4. **Error Handling**: Comprehensive error handling patterns
5. **React Components**: Ready-to-use form components
6. **API Client**: Axios-based client with token management

All endpoints are available through the API Gateway at `/api/v1/auth/*` and can be accessed without authentication for registration and password reset flows.
