import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ChatService } from './chat.service';
import { switchMap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class ChatNavigationService {
  private router = inject(Router);
  private chatService = inject(ChatService);

  /**
   * Start a new chat session with a document
   */
  startChatWithDocument(documentId: string, documentTitle: string) {
    // First create a chat session
    this.chatService
      .createSession(documentId, `Chat about ${documentTitle}`)
      .pipe(
        switchMap((session) => {
          // Then navigate to the chat
          return this.router.navigate(['/chat', session.id]);
        })
      )
      .subscribe({
        error: (error) => {
          console.error('Failed to start chat:', error);
        },
      });
  }

  /**
   * Navigate to an existing chat session
   */
  navigateToChat(sessionId: string) {
    this.router.navigate(['/chat', sessionId]);
  }

  /**
   * Navigate to the chat list
   */
  navigateToChatList() {
    this.router.navigate(['/chat']);
  }
}