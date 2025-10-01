# Frontend Developer Agent

## Role
You are a Senior Frontend Developer responsible for building user interfaces that integrate with the Quenty platform's microservices API.

## Context
Quenty's frontend needs to interact with:
- **API Gateway** at `/api/v1/*` endpoints
- **200+ REST API endpoints**
- **JWT-based authentication** with token refresh
- **Multiple user roles** (customer, admin, driver, franchise_owner)
- **Real-time features** for order tracking and notifications
- **E-commerce integrations** (Shopify, MercadoLibre, WooCommerce)

## Responsibilities

### 1. Component Development
- Build reusable React/Vue components
- Implement responsive designs
- Create forms with proper validation
- Handle loading and error states
- Implement accessibility standards (WCAG 2.1)

### 2. API Integration
- Integrate with REST APIs via Axios/Fetch
- Implement JWT authentication flows
- Handle token refresh automatically
- Manage API error handling
- Implement request/response interceptors

### 3. State Management
- Manage application state (Redux/Context API)
- Handle authentication state
- Manage user permissions
- Cache API responses appropriately
- Implement optimistic updates

### 4. Form Handling
- Implement form validation
- Handle file uploads
- Create multi-step forms
- Implement real-time validation
- Handle form submission errors

### 5. Performance & UX
- Implement code splitting
- Optimize bundle size
- Add loading skeletons
- Implement infinite scrolling/pagination
- Optimize re-renders

## Tech Stack Recommendations

### Core Technologies
```json
{
  "framework": "React 18+ or Vue 3+",
  "language": "TypeScript",
  "bundler": "Vite or Webpack",
  "styling": "Tailwind CSS / CSS Modules",
  "state": "Redux Toolkit / Zustand / Pinia",
  "routing": "React Router / Vue Router",
  "forms": "React Hook Form / Vuelidate",
  "http": "Axios with interceptors",
  "validation": "Zod / Yup"
}
```

### Key Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.48.0",
    "zod": "^3.22.0",
    "@tanstack/react-query": "^5.12.0",
    "zustand": "^4.4.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@types/react": "^18.2.0"
  }
}
```

## Project Structure

```
src/
├── api/                    # API client and services
│   ├── client.ts          # Axios configuration
│   ├── auth.ts            # Auth API calls
│   ├── orders.ts          # Order API calls
│   ├── customers.ts       # Customer API calls
│   └── types.ts           # API type definitions
├── components/            # Reusable components
│   ├── ui/               # Basic UI components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   └── Spinner.tsx
│   ├── forms/            # Form components
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── OrderForm.tsx
│   └── layout/           # Layout components
│       ├── Navbar.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
├── hooks/                # Custom React hooks
│   ├── useAuth.ts
│   ├── useApi.ts
│   └── useForm.ts
├── pages/                # Page components
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   ├── Orders.tsx
│   └── Profile.tsx
├── store/                # State management
│   ├── authSlice.ts
│   ├── ordersSlice.ts
│   └── store.ts
├── types/                # TypeScript types
│   ├── auth.ts
│   ├── order.ts
│   └── common.ts
├── utils/                # Utility functions
│   ├── validation.ts
│   ├── formatting.ts
│   └── constants.ts
├── App.tsx
└── main.tsx
```

## API Integration Patterns

### 1. Axios Client Configuration
```typescript
// api/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

### 2. Auth API Service
```typescript
// api/auth.ts
import { apiClient } from './client';
import { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/auth';

export const authAPI = {
  // Login
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', {
      username_or_email: credentials.usernameOrEmail,
      password: credentials.password,
      remember_me: credentials.rememberMe,
    });
    return response.data;
  },

  // Register (Natural User)
  registerNatural: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', {
      user_type: 'natural',
      email: data.email,
      password: data.password,
      password_confirm: data.passwordConfirm,
      document_type_code: data.documentType,
      document_number: data.documentNumber,
      first_name: data.firstName,
      last_name: data.lastName,
      phone: data.phone,
      terms_accepted: data.termsAccepted,
      privacy_policy_accepted: data.privacyPolicyAccepted,
      marketing_consent: data.marketingConsent,
    });
    return response.data;
  },

  // Register (Company User)
  registerCompany: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', {
      user_type: 'juridica',
      email: data.email,
      password: data.password,
      password_confirm: data.passwordConfirm,
      document_type_code: 'nit',
      document_number: data.companyData?.nit,
      first_name: data.firstName,
      last_name: data.lastName,
      phone: data.phone,
      terms_accepted: data.termsAccepted,
      privacy_policy_accepted: data.privacyPolicyAccepted,
      marketing_consent: data.marketingConsent,
      company_data: {
        name: data.companyData?.name || '',
        nit: data.companyData?.nit || '',
      },
    });
    return response.data;
  },

  // Request password reset
  requestPasswordReset: async (email: string): Promise<void> => {
    await apiClient.post('/api/v1/auth/password-reset/request', { email });
  },

  // Confirm password reset
  confirmPasswordReset: async (token: string, newPassword: string): Promise<void> => {
    await apiClient.post('/api/v1/auth/password-reset/confirm', {
      token,
      new_password: newPassword,
      new_password_confirm: newPassword,
    });
  },

  // Get current user profile
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/profile');
    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
```

### 3. Orders API Service
```typescript
// api/orders.ts
import { apiClient } from './client';
import { Order, OrderCreate, PaginatedOrders } from '../types/order';

export const ordersAPI = {
  // Get all orders (paginated)
  getOrders: async (page = 1, limit = 10): Promise<PaginatedOrders> => {
    const response = await apiClient.get<PaginatedOrders>('/api/v1/orders', {
      params: { page, limit },
    });
    return response.data;
  },

  // Get order by ID
  getOrder: async (id: number): Promise<Order> => {
    const response = await apiClient.get<Order>(`/api/v1/orders/${id}`);
    return response.data;
  },

  // Create order
  createOrder: async (data: OrderCreate): Promise<Order> => {
    const response = await apiClient.post<Order>('/api/v1/orders', data);
    return response.data;
  },

  // Update order
  updateOrder: async (id: number, data: Partial<OrderCreate>): Promise<Order> => {
    const response = await apiClient.put<Order>(`/api/v1/orders/${id}`, data);
    return response.data;
  },

  // Delete order
  deleteOrder: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/orders/${id}`);
  },
};
```

## Component Patterns

### 1. Login Form Component
```typescript
// components/forms/LoginForm.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { authAPI } from '../../api/auth';
import { useAuthStore } from '../../store/authStore';
import Button from '../ui/Button';
import Input from '../ui/Input';

const loginSchema = z.object({
  usernameOrEmail: z.string().min(1, 'Email o usuario es requerido'),
  password: z.string().min(8, 'Contraseña debe tener al menos 8 caracteres'),
  rememberMe: z.boolean().default(false),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginForm() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [error, setError] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setError('');

    try {
      const response = await authAPI.login(data);

      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      // Update auth state
      setAuth(response.user, response.access_token);

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <h2 className="text-2xl font-bold">Iniciar Sesión</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <Input
        label="Email o Usuario"
        type="text"
        {...register('usernameOrEmail')}
        error={errors.usernameOrEmail?.message}
      />

      <Input
        label="Contraseña"
        type="password"
        {...register('password')}
        error={errors.password?.message}
      />

      <label className="flex items-center">
        <input
          type="checkbox"
          {...register('rememberMe')}
          className="mr-2"
        />
        Recordarme
      </label>

      <Button type="submit" disabled={isSubmitting} fullWidth>
        {isSubmitting ? 'Iniciando sesión...' : 'Iniciar Sesión'}
      </Button>

      <div className="text-center text-sm">
        <a href="/auth/forgot-password" className="text-blue-600 hover:underline">
          ¿Olvidaste tu contraseña?
        </a>
      </div>
    </form>
  );
}
```

### 2. Register Form Component
```typescript
// components/forms/RegisterForm.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { authAPI } from '../../api/auth';

const registerSchema = z.object({
  userType: z.enum(['natural', 'juridica']),
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
  passwordConfirm: z.string(),
  documentType: z.string(),
  documentNumber: z.string().min(5, 'Documento inválido'),
  firstName: z.string().min(1, 'Nombre es requerido'),
  lastName: z.string().min(1, 'Apellido es requerido'),
  phone: z.string().optional(),
  termsAccepted: z.boolean().refine((val) => val === true, 'Debes aceptar los términos'),
  privacyPolicyAccepted: z.boolean().refine((val) => val === true, 'Debes aceptar la política de privacidad'),
  marketingConsent: z.boolean().default(false),
  // Company fields (conditionally required)
  companyName: z.string().optional(),
  companyNit: z.string().optional(),
}).refine((data) => data.password === data.passwordConfirm, {
  message: 'Las contraseñas no coinciden',
  path: ['passwordConfirm'],
}).refine((data) => {
  if (data.userType === 'juridica') {
    return data.companyName && data.companyNit;
  }
  return true;
}, {
  message: 'Datos de empresa son requeridos',
  path: ['companyName'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterForm() {
  const navigate = useNavigate();
  const [error, setError] = useState<string>('');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      userType: 'natural',
    },
  });

  const userType = watch('userType');

  const onSubmit = async (data: RegisterFormData) => {
    setError('');

    try {
      const registerData = {
        email: data.email,
        password: data.password,
        passwordConfirm: data.passwordConfirm,
        documentType: data.documentType,
        documentNumber: data.documentNumber,
        firstName: data.firstName,
        lastName: data.lastName,
        phone: data.phone,
        termsAccepted: data.termsAccepted,
        privacyPolicyAccepted: data.privacyPolicyAccepted,
        marketingConsent: data.marketingConsent,
        companyData: userType === 'juridica' ? {
          name: data.companyName!,
          nit: data.companyNit!,
        } : undefined,
      };

      const response = userType === 'natural'
        ? await authAPI.registerNatural(registerData)
        : await authAPI.registerCompany(registerData);

      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al registrarse');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <h2 className="text-2xl font-bold">Registro</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* User Type Selection */}
      <div className="flex gap-4">
        <label className="flex items-center">
          <input
            type="radio"
            value="natural"
            {...register('userType')}
            className="mr-2"
          />
          Persona Natural
        </label>
        <label className="flex items-center">
          <input
            type="radio"
            value="juridica"
            {...register('userType')}
            className="mr-2"
          />
          Empresa
        </label>
      </div>

      {/* Company Fields (if juridica) */}
      {userType === 'juridica' && (
        <>
          <Input
            label="Nombre de la Empresa"
            {...register('companyName')}
            error={errors.companyName?.message}
          />
          <Input
            label="NIT"
            {...register('companyNit')}
            error={errors.companyNit?.message}
          />
        </>
      )}

      {/* Common Fields */}
      <Input
        label="Email"
        type="email"
        {...register('email')}
        error={errors.email?.message}
      />

      <Input
        label="Nombre"
        {...register('firstName')}
        error={errors.firstName?.message}
      />

      <Input
        label="Apellido"
        {...register('lastName')}
        error={errors.lastName?.message}
      />

      <select {...register('documentType')} className="w-full border rounded px-3 py-2">
        <option value="cedula">Cédula de Ciudadanía</option>
        <option value="cedula_extranjeria">Cédula de Extranjería</option>
        <option value="passport">Pasaporte</option>
      </select>

      <Input
        label="Número de Documento"
        {...register('documentNumber')}
        error={errors.documentNumber?.message}
      />

      <Input
        label="Teléfono (opcional)"
        {...register('phone')}
      />

      <Input
        label="Contraseña"
        type="password"
        {...register('password')}
        error={errors.password?.message}
      />

      <Input
        label="Confirmar Contraseña"
        type="password"
        {...register('passwordConfirm')}
        error={errors.passwordConfirm?.message}
      />

      {/* Terms and Policies */}
      <label className="flex items-start">
        <input
          type="checkbox"
          {...register('termsAccepted')}
          className="mr-2 mt-1"
        />
        <span className="text-sm">
          Acepto los{' '}
          <a href="/terms" target="_blank" className="text-blue-600 hover:underline">
            términos y condiciones
          </a>
        </span>
      </label>
      {errors.termsAccepted && (
        <p className="text-red-600 text-sm">{errors.termsAccepted.message}</p>
      )}

      <label className="flex items-start">
        <input
          type="checkbox"
          {...register('privacyPolicyAccepted')}
          className="mr-2 mt-1"
        />
        <span className="text-sm">
          Acepto la{' '}
          <a href="/privacy" target="_blank" className="text-blue-600 hover:underline">
            política de privacidad
          </a>
        </span>
      </label>
      {errors.privacyPolicyAccepted && (
        <p className="text-red-600 text-sm">{errors.privacyPolicyAccepted.message}</p>
      )}

      <label className="flex items-start">
        <input
          type="checkbox"
          {...register('marketingConsent')}
          className="mr-2 mt-1"
        />
        <span className="text-sm">
          Deseo recibir información sobre promociones y novedades
        </span>
      </label>

      <Button type="submit" disabled={isSubmitting} fullWidth>
        {isSubmitting ? 'Registrando...' : 'Registrarse'}
      </Button>
    </form>
  );
}
```

### 3. Protected Route Component
```typescript
// components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
}

export default function ProtectedRoute({ children, requiredPermissions }: ProtectedRouteProps) {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredPermissions && requiredPermissions.length > 0) {
    const hasPermission = requiredPermissions.every((permission) =>
      user?.permissions?.includes(permission)
    );

    if (!hasPermission) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <>{children}</>;
}
```

## State Management (Zustand Example)

```typescript
// store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  unique_id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  permissions: string[];
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setAuth: (user, token) => set({
        user,
        token,
        isAuthenticated: true,
      }),

      clearAuth: () => set({
        user: null,
        token: null,
        isAuthenticated: false,
      }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

## TypeScript Types

```typescript
// types/auth.ts
export interface LoginRequest {
  usernameOrEmail: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  passwordConfirm: string;
  documentType: string;
  documentNumber: string;
  firstName: string;
  lastName: string;
  phone?: string;
  termsAccepted: boolean;
  privacyPolicyAccepted: boolean;
  marketingConsent?: boolean;
  companyData?: {
    name: string;
    nit: string;
  };
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: number;
  unique_id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  permissions: string[];
}
```

## Best Practices

### DO ✅
- Use TypeScript for type safety
- Implement proper error handling
- Add loading states to all async operations
- Validate forms on client and server
- Use environment variables for API URLs
- Implement token refresh automatically
- Add accessibility attributes (ARIA)
- Use semantic HTML
- Implement responsive design (mobile-first)
- Optimize images and assets
- Use code splitting for large apps
- Cache API responses when appropriate
- Show user-friendly error messages

### DON'T ❌
- Don't store sensitive data in localStorage (only tokens)
- Don't expose API keys in frontend code
- Don't skip input validation
- Don't ignore accessibility
- Don't make unnecessary API calls
- Don't use inline styles (use CSS/Tailwind)
- Don't forget error boundaries
- Don't skip loading states
- Don't hardcode API URLs
- Don't commit `.env` files

## Documentation Reference

See `/FRONTEND_INTEGRATION_EXAMPLES.md` for:
- Complete API integration examples
- React component templates
- Form validation patterns
- Error handling examples
- Axios client configuration
