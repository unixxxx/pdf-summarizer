import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PDFSummaryHistoryItem {
  id: string;
  fileName: string;
  fileSize: number;
  summary: string;
  createdAt: string;
}

export interface PDFSummaryRequest {
  summary_length?: number;
  summary_format?: string;
  additional_instructions?: string;
}

export interface TextSummarizeRequest {
  text: string;
  summary_length?: number;
  summary_format?: string;
  additional_instructions?: string;
}

export interface SummarizeResponse {
  summary: string;
  id?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);

  uploadPDF(file: File, options?: PDFSummaryRequest): Observable<SummarizeResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options?.summary_length) {
      formData.append('summary_length', options.summary_length.toString());
    }
    if (options?.summary_format) {
      formData.append('summary_format', options.summary_format);
    }
    if (options?.additional_instructions) {
      formData.append('additional_instructions', options.additional_instructions);
    }

    return this.http.post<SummarizeResponse>('/api/v1/pdf/summarize', formData);
  }

  summarizeText(request: TextSummarizeRequest): Observable<SummarizeResponse> {
    return this.http.post<SummarizeResponse>('/api/v1/summarization/text', request);
  }

  getHistory(): Observable<PDFSummaryHistoryItem[]> {
    return this.http.get<PDFSummaryHistoryItem[]>('/api/v1/pdf/history');
  }

  deleteSummary(id: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/pdf/history/${id}`);
  }
}