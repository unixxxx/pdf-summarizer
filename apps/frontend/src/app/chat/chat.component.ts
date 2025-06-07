import { Component, OnInit, inject, signal, effect, viewChild, ElementRef, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ChatMessage } from '../chat.service';
import { ChatStore } from './chat.store';
import { ConfirmationModalComponent } from '../shared/confirmation-modal.component';

interface ChatMessageDisplay extends ChatMessage {
  isUser: boolean;
  displayName: string;
  chunksCount: number;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, ConfirmationModalComponent],
  template: `
    <div class="max-w-7xl mx-auto h-[calc(100vh-5rem)] flex">
      <!-- Sidebar -->
      <div class="w-80 border-r border-border/50 flex-col bg-background/50 hidden sm:flex">
        <div class="p-4 border-b border-border/50">
          <button
            (click)="createNewChat()"
            class="w-full px-4 py-2 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
          >
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Clear Chat
          </button>
        </div>
        
        <div class="flex-1 overflow-y-auto">
          @if (isLoadingSessions()) {
            <div class="p-4 text-center text-muted-foreground">
              <div class="inline-flex items-center">
                <div class="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mr-2"></div>
                Loading chats...
              </div>
            </div>
          } @else if (sessions().length === 0) {
            <div class="p-8 text-center text-muted-foreground">
              <svg class="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p class="text-sm">No chat sessions yet</p>
              <p class="text-xs mt-1">Upload a PDF to start chatting</p>
            </div>
          } @else {
            @for (session of sessions(); track session.id) {
              <button
                (click)="selectChat(session.id)"
                [class.bg-muted]="selectedChatId() === session.id"
                class="w-full p-4 text-left hover:bg-muted/50 transition-colors border-b border-border/30 group"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <h3 class="font-medium text-sm text-foreground truncate">
                      {{ session.title }}
                    </h3>
                    <p class="text-xs text-muted-foreground mt-1 truncate">
                      {{ session.document_filename }}
                    </p>
                    @if (session.last_message) {
                      <p class="text-xs text-muted-foreground mt-2 line-clamp-2">
                        {{ session.last_message }}
                      </p>
                    }
                  </div>
                  <button
                    (click)="confirmDeleteChat(session.id, $event)"
                    class="ml-2 p-1 text-muted-foreground hover:text-error hover:bg-error/10 rounded transition-all opacity-0 group-hover:opacity-100"
                    title="Delete chat"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </button>
            }
          }
        </div>
      </div>
      
      <!-- Chat Area -->
      <div class="flex-1 flex flex-col">
        @if (selectedChatId()) {
          <!-- Chat Header -->
          <div class="p-4 border-b border-border/50 bg-background/50">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-foreground">
                {{ chatTitle() }}
              </h2>
              <!-- Mobile menu button -->
              <button
                (click)="toggleMobileSidebar()"
                class="sm:hidden p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
          
          <!-- Messages -->
          <div #messagesContainer class="flex-1 overflow-y-auto p-4 space-y-4">
            @for (msg of displayMessages(); track msg.id) {
              <div [class.justify-end]="msg.isUser" class="flex">
                <div
                  [ngClass]="{
                    'bg-primary-100 dark:bg-primary-900/30': msg.isUser,
                    'glass': !msg.isUser,
                    'max-w-[80%]': true
                  }"
                  class="rounded-xl p-4"
                >
                  <div class="flex items-start gap-3">
                    <div
                      [ngClass]="{
                        'bg-gradient-to-br from-primary-400 to-accent-400': msg.isUser,
                        'bg-muted': !msg.isUser
                      }"
                      class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                    >
                      @if (msg.isUser) {
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      } @else {
                        <svg class="w-5 h-5 text-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                      }
                    </div>
                    <div class="flex-1">
                      <p class="text-xs text-muted-foreground mb-1">
                        {{ msg.displayName }}
                      </p>
                      <div class="text-foreground whitespace-pre-wrap">{{ msg.content }}</div>
                      @if (msg.chunksCount > 0) {
                        <div class="mt-2 text-xs text-muted-foreground">
                          <details class="group">
                            <summary class="cursor-pointer inline-flex items-center hover:text-foreground transition-colors">
                              <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              Used {{ msg.chunksCount }} document excerpts
                              <svg class="w-3 h-3 ml-1 transform transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                              </svg>
                            </summary>
                            <div class="mt-2 pl-4 space-y-1">
                              @for (chunk of msg.message_metadata?.chunks_used || []; track chunk.chunk_id; let i = $index) {
                                <div class="text-xs">
                                  <span class="font-medium">Excerpt {{ i + 1 }}</span>
                                  <span class="text-muted-foreground/70">({{ (chunk.similarity * 100).toFixed(1) }}% relevant)</span>
                                </div>
                              }
                            </div>
                          </details>
                        </div>
                      }
                    </div>
                  </div>
                </div>
              </div>
            }
            
            @if (isTyping()) {
              <div class="flex">
                <div class="glass rounded-xl p-4 max-w-[80%]">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                      <svg class="w-5 h-5 text-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div class="flex items-center gap-1">
                      <div class="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                      <div class="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                      <div class="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style="animation-delay: 300ms"></div>
                    </div>
                  </div>
                </div>
              </div>
            }
          </div>
          
          <!-- Input Area -->
          <div class="border-t border-border/50 p-4 bg-background/50">
            <form (submit)="sendMessage($event)" class="flex gap-2">
              <input
                [(ngModel)]="messageText"
                [disabled]="isTyping()"
                type="text"
                name="message"
                placeholder="Ask a question about the document..."
                class="flex-1 px-4 py-2 bg-muted/50 border border-border/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent transition-all"
              />
              <button
                type="submit"
                [disabled]="!messageText().trim() || isTyping()"
                class="px-6 py-2 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 disabled:from-muted disabled:to-muted text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all disabled:transform-none disabled:shadow-none"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </form>
          </div>
        } @else {
          <!-- Empty State -->
          <div class="flex-1 flex items-center justify-center p-8">
            <div class="text-center max-w-md">
              <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 mb-4">
                <svg class="w-10 h-10 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 class="text-xl font-semibold text-foreground mb-2">Start a Conversation</h3>
              <p class="text-muted-foreground mb-6">
                To start a chat, you need to select a document first
              </p>
              <div class="space-y-3">
                <a
                  routerLink="/app/history"
                  class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
                >
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Choose from Existing Documents
                </a>
                <p class="text-sm text-muted-foreground">or</p>
                <a
                  routerLink="/app/upload"
                  class="inline-flex items-center px-6 py-3 bg-muted hover:bg-muted/80 text-foreground font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
                >
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload a New PDF
                </a>
              </div>
            </div>
          </div>
        }
      </div>
      
      <!-- Mobile Sidebar Overlay -->
      @if (showMobileSidebar()) {
        <div
          class="fixed inset-0 bg-black/50 sm:hidden z-40"
          (click)="toggleMobileSidebar()"
          (keydown.escape)="toggleMobileSidebar()"
          tabindex="0"
          role="button"
          aria-label="Close sidebar"
        ></div>
        <div class="fixed left-0 top-0 h-full w-80 bg-background shadow-xl sm:hidden z-50">
          <!-- Copy of sidebar content here for mobile -->
        </div>
      }
      
      <!-- Delete Confirmation Modal -->
      <app-confirmation-modal
        [isOpen]="showDeleteModal()"
        title="Delete Chat"
        message="Are you sure you want to delete this chat? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        (confirmed)="deleteChat()"
        (cancelled)="cancelDelete()"
      />
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
    }
  `]
})
export class ChatComponent implements OnInit {
  private messagesContainer = viewChild<ElementRef>('messagesContainer');
  
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  readonly store = inject(ChatStore);
  
  // Local UI state
  messageText = signal('');
  showMobileSidebar = signal(false);
  showDeleteModal = signal(false);
  chatToDelete = signal<string | null>(null);
  
  // Store selectors
  sessions = this.store.sessions;
  selectedChatId = this.store.selectedChatId;
  currentChat = this.store.currentChat;
  chatTitle = this.store.chatTitle;
  currentMessages = this.store.currentMessages;
  isLoadingSessions = this.store.isLoadingSessions;
  isTyping = this.store.isSendingMessage;
  error = this.store.error;
  
  displayMessages = computed((): ChatMessageDisplay[] => {
    return this.currentMessages().map(msg => ({
      ...msg,
      isUser: msg.role === 'user',
      displayName: msg.role === 'user' ? 'You' : 'Assistant',
      chunksCount: msg.message_metadata?.chunks_used?.length || 0
    }));
  });
  
  constructor() {
    // Auto-scroll to bottom when new messages arrive
    effect(() => {
      const messages = this.currentMessages();
      if (messages.length > 0 && this.messagesContainer()) {
        setTimeout(() => {
          this.scrollToBottom();
        }, 100);
      }
    });
    
    // Show error messages
    effect(() => {
      const error = this.error();
      if (error) {
        console.error('Chat error:', error);
        // You could show a toast notification here
        setTimeout(() => this.store.clearError(), 5000);
      }
    });
  }
  
  ngOnInit() {
    // Load chat sessions
    this.store.loadSessions();
    
    // Check if we have a chat ID in the route
    this.route.params.subscribe(params => {
      if (params['chatId']) {
        this.store.loadChat(params['chatId']);
      }
    });
  }
  
  createNewChat() {
    // Clear current selection to show the empty state with instructions
    this.store.clearCurrentChat();
    this.router.navigate(['/app/chat']);
  }
  
  selectChat(chatId: string) {
    // Only navigate, the route subscription will handle loading
    this.router.navigate(['/app/chat', chatId]);
  }
  
  sendMessage(event: Event) {
    event.preventDefault();
    
    const message = this.messageText().trim();
    if (!message || this.isTyping()) return;
    
    const chatId = this.selectedChatId();
    if (!chatId) return;
    
    // Clear input immediately
    this.messageText.set('');
    
    // Send message through store
    this.store.sendMessage({ chatId, message });
    
    // Scroll to bottom after a brief delay
    setTimeout(() => this.scrollToBottom(), 100);
  }
  
  confirmDeleteChat(chatId: string, event: Event) {
    event.stopPropagation();
    this.chatToDelete.set(chatId);
    this.showDeleteModal.set(true);
  }
  
  deleteChat() {
    const chatId = this.chatToDelete();
    if (chatId) {
      this.store.deleteChat(chatId);
    }
    this.cancelDelete();
  }
  
  cancelDelete() {
    this.showDeleteModal.set(false);
    this.chatToDelete.set(null);
  }
  
  toggleMobileSidebar() {
    this.showMobileSidebar.update(show => !show);
  }
  
  private scrollToBottom() {
    const container = this.messagesContainer();
    if (container) {
      const element = container.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }
}