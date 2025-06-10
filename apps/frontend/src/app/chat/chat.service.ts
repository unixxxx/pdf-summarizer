import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Chat, ChatMessage, ChatDto, ChatMessageDto } from './chat.model';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/chat';

  createSession(documentId: string, title?: string): Observable<Chat> {
    return this.http
      .post<ChatDto>(`${this.baseUrl}/sessions`, {
        document_id: documentId,
        title,
      })
      .pipe(map((dto) => Chat.fromDto(dto)));
  }

  findOrCreateSession(documentId: string, title?: string): Observable<Chat> {
    return this.http
      .post<ChatDto>(`${this.baseUrl}/sessions/find-or-create`, {
        document_id: documentId,
        title,
      })
      .pipe(map((dto) => Chat.fromDto(dto)));
  }

  getSessions(): Observable<Chat[]> {
    return this.http
      .get<ChatDto[]>(`${this.baseUrl}/sessions`)
      .pipe(map((dtos) => dtos.map((dto) => Chat.fromDto(dto))));
  }

  getSessionWithMessages(
    chatId: string
  ): Observable<{ chat: Chat; messages: ChatMessage[] }> {
    return this.http
      .get<{ chat: ChatDto; messages: ChatMessageDto[] }>(
        `${this.baseUrl}/sessions/${chatId}`
      )
      .pipe(
        map((response) => ({
          chat: Chat.fromDto(response.chat),
          messages: response.messages.map((msg) => ChatMessage.fromDto(msg)),
        }))
      );
  }

  sendMessage(chatId: string, message: string): Observable<ChatMessage[]> {
    return this.http
      .post<ChatMessageDto[]>(`${this.baseUrl}/sessions/${chatId}/messages`, {
        message,
      })
      .pipe(map((dtos) => dtos.map((dto) => ChatMessage.fromDto(dto))));
  }

  deleteSession(chatId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/sessions/${chatId}`);
  }
}
