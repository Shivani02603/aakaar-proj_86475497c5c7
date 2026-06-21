import axios, { AxiosInstance } from 'axios';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
});

// Request interceptor: Add Authorization header if token exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// TypeScript interfaces for request/response types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
}

export interface SessionCreateRequest {
  name: string;
}

export interface SessionResponse {
  id: string;
  name: string;
  createdAt: string;
}

export interface FileUploadRequest {
  filename: string;
  original_filename: string;
  file_size: number;
}

export interface FileResponse {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  createdAt: string;
}

export interface MessageResponse {
  id: string;
  role: string;
  content: string;
  createdAt: string;
}

export interface AiQueryRequest {
  query: string;
  session_id: string;
}

export interface AiQueryResponse {
  answer: string;
  citations: Array<{ source: string; snippet: string }>;
}

// API client functions
export const createSession = (data: SessionCreateRequest) => api.post<SessionResponse>('/api/sessions', data);

export const listSessions = () => api.get<SessionResponse[]>('/api/sessions');

export const getSession = (session_id: string) => api.get<SessionResponse>(`/api/sessions/${session_id}`);

export const uploadFile = (session_id: string, data: FileUploadRequest) =>
  api.post<FileResponse>(`/api/sessions/${session_id}/files`, data);

export const listFiles = (session_id: string) =>
  api.get<FileResponse[]>(`/api/sessions/${session_id}/files`);

export const getMessages = (session_id: string) =>
  api.get<MessageResponse[]>(`/api/sessions/${session_id}/messages`);

export const ingestDocuments = (data: FormData) => api.post('/api/ai/ingest', data);

export const aiQuery = (data: AiQueryRequest) => api.post<AiQueryResponse>('/api/ai/query', data);