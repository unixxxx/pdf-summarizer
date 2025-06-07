import { computed, inject } from '@angular/core';
import { tapResponse } from '@ngrx/operators';
import {
  patchState,
  signalStore,
  withComputed,
  withMethods,
  withState,
} from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, switchMap, tap } from 'rxjs';
import { ChatService, ChatSession, ChatMessage, ChatWithMessages } from '../chat.service';

interface ChatState {
  sessions: ChatSession[];
  currentChat: ChatWithMessages | null;
  selectedChatId: string | null;
  isLoadingSessions: boolean;
  isLoadingChat: boolean;
  isSendingMessage: boolean;
  error: string | null;
}

const initialState: ChatState = {
  sessions: [],
  currentChat: null,
  selectedChatId: null,
  isLoadingSessions: false,
  isLoadingChat: false,
  isSendingMessage: false,
  error: null,
};

export const ChatStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    currentMessages: computed(() => store.currentChat()?.messages || []),
    chatTitle: computed(() => store.currentChat()?.chat.title || 'Chat'),
    hasSessions: computed(() => store.sessions().length > 0),
    isLoading: computed(() => 
      store.isLoadingSessions() || store.isLoadingChat() || store.isSendingMessage()
    ),
  })),
  withMethods((store, chatService = inject(ChatService)) => ({
    loadSessions: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { isLoadingSessions: true, error: null })),
        switchMap(() =>
          chatService.getChatSessions().pipe(
            tapResponse({
              next: (sessions) =>
                patchState(store, { sessions, isLoadingSessions: false }),
              error: () =>
                patchState(store, {
                  error: 'Failed to load chat sessions',
                  isLoadingSessions: false,
                }),
            })
          )
        )
      )
    ),

    loadChat: rxMethod<string>(
      pipe(
        tap((chatId) => 
          patchState(store, { 
            selectedChatId: chatId, 
            isLoadingChat: true, 
            error: null 
          })
        ),
        switchMap((chatId) =>
          chatService.getChatWithMessages(chatId).pipe(
            tapResponse({
              next: (chat) =>
                patchState(store, { currentChat: chat, isLoadingChat: false }),
              error: () =>
                patchState(store, {
                  error: 'Failed to load chat',
                  isLoadingChat: false,
                }),
            })
          )
        )
      )
    ),

    sendMessage: rxMethod<{ chatId: string; message: string }>(
      pipe(
        tap(() => patchState(store, { isSendingMessage: true, error: null })),
        tap(({ message, chatId }) => {
          // Optimistically add user message
          const tempUserMessage: ChatMessage = {
            id: 'temp-' + Date.now(),
            chat_id: chatId,
            role: 'user',
            content: message,
            created_at: new Date().toISOString(),
          };

          const currentChat = store.currentChat();
          if (currentChat) {
            patchState(store, {
              currentChat: {
                ...currentChat,
                messages: [...currentChat.messages, tempUserMessage],
              },
            });
          }
        }),
        switchMap(({ chatId, message }) =>
          chatService.sendMessage(chatId, message).pipe(
            tapResponse({
              next: (responses) => {
                const currentChat = store.currentChat();
                if (currentChat) {
                  // Remove temp message and add both user and AI messages
                  const messagesWithoutTemp = currentChat.messages.filter(
                    (m) => !m.id.startsWith('temp-')
                  );
                  patchState(store, {
                    currentChat: {
                      ...currentChat,
                      messages: [...messagesWithoutTemp, ...responses],
                    },
                    isSendingMessage: false,
                  });
                }
              },
              error: () => {
                // Remove temp message on error
                const currentChat = store.currentChat();
                if (currentChat) {
                  patchState(store, {
                    currentChat: {
                      ...currentChat,
                      messages: currentChat.messages.filter(
                        (m) => !m.id.startsWith('temp-')
                      ),
                    },
                    error: 'Failed to send message',
                    isSendingMessage: false,
                  });
                }
              },
            })
          )
        )
      )
    ),

    createChatSession: (documentId: string, title?: string) => {
      return chatService.createChatSession(documentId, title);
    },

    deleteChat: rxMethod<string>(
      pipe(
        switchMap((chatId) =>
          chatService.deleteChat(chatId).pipe(
            tapResponse({
              next: () => {
                patchState(store, {
                  sessions: store.sessions().filter((s) => s.id !== chatId),
                });
                if (store.selectedChatId() === chatId) {
                  patchState(store, {
                    selectedChatId: null,
                    currentChat: null,
                  });
                }
              },
              error: () =>
                patchState(store, { error: 'Failed to delete chat' }),
            })
          )
        )
      )
    ),

    clearError: () => patchState(store, { error: null }),

    clearCurrentChat: () => patchState(store, { 
      currentChat: null, 
      selectedChatId: null 
    }),
  }))
);