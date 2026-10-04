import axios from 'axios';
import type {
  ChatResponse,
  FieldLineageResponse,
  ImpactResponse,
  LineageResponse,
  ObjectMetadata,
  ParsedCSN,
  UploadResponse,
} from '../types/metadata';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  async checkHealth(): Promise<{ status: string; app: string }> {
    const res = await client.get('/api/health');
    return res.data;
  },

  async uploadCSN(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async loadSample(sampleType: 'sample' | 'full' = 'sample'): Promise<UploadResponse> {
    const res = await client.post(`/api/load-sample?sample_type=${sampleType}`);
    return res.data;
  },

  async getMetadata(sessionId: string): Promise<ParsedCSN> {
    const res = await client.get(`/api/metadata/${sessionId}`);
    return res.data;
  },

  async getObjects(sessionId: string): Promise<ObjectMetadata[]> {
    const res = await client.get(`/api/objects/${sessionId}`);
    return res.data;
  },

  async getObject(sessionId: string, objectName: string): Promise<ObjectMetadata> {
    const encoded = encodeURIComponent(objectName);
    const res = await client.get(`/api/object/${sessionId}/${encoded}`);
    return res.data;
  },

  async getLineage(sessionId: string, objectName: string): Promise<LineageResponse> {
    const encoded = encodeURIComponent(objectName);
    const res = await client.get(`/api/lineage/${sessionId}/${encoded}`);
    return res.data;
  },

  async getImpact(sessionId: string, objectName: string): Promise<ImpactResponse> {
    const encoded = encodeURIComponent(objectName);
    const res = await client.get(`/api/impact/${sessionId}/${encoded}`);
    return res.data;
  },

  async getFieldLineage(
    sessionId: string,
    objectName: string,
    fieldName: string
  ): Promise<FieldLineageResponse> {
    const encObj = encodeURIComponent(objectName);
    const encField = encodeURIComponent(fieldName);
    const res = await client.get(`/api/field-lineage/${sessionId}/${encObj}/${encField}`);
    return res.data;
  },

  async chat(sessionId: string, message: string): Promise<ChatResponse> {
    const res = await client.post('/api/chat', {
      session_id: sessionId,
      message,
    });
    return res.data;
  },
};
