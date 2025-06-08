import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatSession {
  id: string;
  document_id: string;
  document_filename: string;
  title: string;
  last_message: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_metadata?: {
    chunks_used?: Array<{
      chunk_id: string;
      similarity: number;
      chunk_index: number;
    }>;
    model?: string;
  };
  created_at: string;
}

export interface ChatWithMessages {
  chat: {
    id: string;
    user_id: string;
    document_id: string;
    title: string;
    created_at: string;
    updated_at: string;
  };
  messages: ChatMessage[];
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private http = inject(HttpClient);
  
  createChatSession(documentId: string, title?: string): Observable<{ id: string }> {
    return this.http.post<{ id: string }>('/api/v1/chat/sessions', {
      document_id: documentId,
      title
    });
  }
  
  findOrCreateChatSession(documentId: string, title?: string): Observable<{ id: string }> {
    return this.http.post<{ id: string }>('/api/v1/chat/sessions/find-or-create', {
      document_id: documentId,
      title
    });
  }
  
  getChatSessions(): Observable<ChatSession[]> {
    return this.http.get<ChatSession[]>('/api/v1/chat/sessions');
  }
  
  getChatWithMessages(chatId: string): Observable<ChatWithMessages> {
    return this.http.get<ChatWithMessages>(`/api/v1/chat/sessions/${chatId}`);
  }
  
  sendMessage(chatId: string, message: string): Observable<ChatMessage[]> {
    return this.http.post<ChatMessage[]>(`/api/v1/chat/sessions/${chatId}/messages`, {
      message
    });
  }
  
  deleteChat(chatId: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/chat/sessions/${chatId}`);
  }
}