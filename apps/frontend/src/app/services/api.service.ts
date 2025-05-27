import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  services: Record<string, boolean>;
}

export interface TextSummaryRequest {
  text: string;
  max_length?: number;
}

export interface TextSummaryResponse {
  summary: string;
  original_length: number;
  summary_length: number;
  original_words: number;
  summary_words: number;
  compression_ratio: number;
}

export interface PDFSummaryResponse {
  summary: string;
  metadata?: {
    filename: string;
    pages: number;
    size_bytes: number;
    title?: string;
    author?: string;
  };
  processing_time: number;
  summary_stats: {
    original_length: number;
    summary_length: number;
    original_words: number;
    summary_words: number;
    compression_ratio: number;
  };
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = '/api/v1';

  constructor(private http: HttpClient) {}

  // Health check
  checkHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>('/health');
  }

  // Summarize text
  summarizeText(request: TextSummaryRequest): Observable<TextSummaryResponse> {
    return this.http.post<TextSummaryResponse>(
      `${this.apiUrl}/summarize/text`,
      request
    );
  }

  // Summarize PDF
  summarizePDF(file: File, maxLength?: number): Observable<PDFSummaryResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const params = maxLength ? `?max_length=${maxLength}` : '';

    return this.http.post<PDFSummaryResponse>(
      `${this.apiUrl}/pdf/summarize${params}`,
      formData
    );
  }

  // Extract text from PDF
  extractPDFText(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<any>(
      `${this.apiUrl}/pdf/extract-text`,
      formData
    );
  }
}