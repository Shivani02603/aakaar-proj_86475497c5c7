import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
});

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
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

// TypeScript interfaces
export interface SessionCreateRequest {
  title: string;
}

export interface FileUploadRequest {
  file: File;
}

export interface FileResponse {
  id: string;
  source: string;
  createdAt: string;
}

export interface MessageResponse {
  id: string;
  role: string;
  content: string;
  createdAt: string;
}

export interface SessionResponse {
  id: string;
  title: string;
  createdAt: string;
}

// API client functions
export const createSession = (data: SessionCreateRequest) => api.post('/api/sessions', data);

export const listSessions = () => api.get<SessionResponse[]>('/api/sessions');

export const getSession = (sessionId: string) =>
  api.get<SessionResponse>(`/api/sessions/${sessionId}`);

export const uploadFile = (sessionId: string, data: FileUploadRequest) =>
  api.post<FileResponse>(`/api/sessions/${sessionId}/files`, data);

export const listFiles = (sessionId: string) =>
  api.get<FileResponse[]>(`/api/sessions/${sessionId}/files`);

export const getMessages = (sessionId: string) =>
  api.get<MessageResponse[]>(`/api/sessions/${sessionId}/messages`);

export const ingestDocuments = (data: FormData) =>
  api.post('/api/ai/ingest', data);

export const aiQuery = (data: { query: string; sessionId: string }) =>
  api.post('/api/ai/query', data);