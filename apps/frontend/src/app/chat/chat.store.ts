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
import { ChatService } from './chat.service';
import { Chat, ChatMessage, MessageRole } from './chat.model';

interface ChatState {
  sessions: Chat[];
  currentSession: Chat | null;
  messages: ChatMessage[];
  selectedChatId: string | null;
  isLoadingSessions: boolean;
  isLoadingChat: boolean;
  isSendingMessage: boolean;
  error: string | null;
}

const initialState: ChatState = {
  sessions: [],
  currentSession: null,
  messages: [],
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
    currentMessages: computed(() => store.messages()),
    chatTitle: computed(() => store.currentSession()?.displayTitle || 'Chat'),
    hasSessions: computed(() => store.sessions().length > 0),
    isLoading: computed(
      () =>
        store.isLoadingSessions() ||
        store.isLoadingChat() ||
        store.isSendingMessage()
    ),
    hasActiveChat: computed(() => !!store.currentSession()),
  })),
  withMethods((store, chatService = inject(ChatService)) => ({
    loadSessions: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { isLoadingSessions: true, error: null })),
        switchMap(() =>
          chatService.getSessions().pipe(
            tapResponse({
              next: (sessions) =>
                patchState(store, {
                  sessions: sessions.sort(
                    (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
                  ),
                  isLoadingSessions: false,
                }),
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
            error: null,
          })
        ),
        switchMap((chatId) =>
          chatService.getSessionWithMessages(chatId).pipe(
            tapResponse({
              next: ({ chat, messages }) =>
                patchState(store, {
                  currentSession: chat,
                  messages,
                  isLoadingChat: false,
                }),
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
          const tempUserMessage = new ChatMessage(
            'temp-' + Date.now(),
            chatId,
            MessageRole.USER,
            message,
            new Date()
          );

          patchState(store, {
            messages: [...store.messages(), tempUserMessage],
          });
        }),
        switchMap(({ chatId, message }) =>
          chatService.sendMessage(chatId, message).pipe(
            tapResponse({
              next: (responses) => {
                // Remove temp message and add real responses
                const messagesWithoutTemp = store
                  .messages()
                  .filter((m) => !m.id.startsWith('temp-'));
                patchState(store, {
                  messages: [...messagesWithoutTemp, ...responses],
                  isSendingMessage: false,
                });

                // Update session's last message and timestamp
                const currentSession = store.currentSession();
                if (currentSession && responses.length > 0) {
                  const updatedSession = new Chat(
                    currentSession.id,
                    currentSession.documentId,
                    currentSession.userId,
                    currentSession.title,
                    currentSession.createdAt,
                    new Date(),
                    currentSession.documentFilename,
                    responses[responses.length - 1].content,
                    store.messages().length
                  );
                  patchState(store, { currentSession: updatedSession });
                }
              },
              error: () => {
                // Remove temp message on error
                patchState(store, {
                  messages: store
                    .messages()
                    .filter((m) => !m.id.startsWith('temp-')),
                  error: 'Failed to send message',
                  isSendingMessage: false,
                });
              },
            })
          )
        )
      )
    ),

    createChat: (documentId: string, title?: string) => {
      return chatService.createSession(documentId, title);
    },

    findOrCreateChat: (documentId: string, title?: string) => {
      return chatService.findOrCreateSession(documentId, title);
    },

    deleteChat: rxMethod<string>(
      pipe(
        switchMap((chatId) =>
          chatService.deleteSession(chatId).pipe(
            tapResponse({
              next: () => {
                patchState(store, {
                  sessions: store.sessions().filter((s) => s.id !== chatId),
                });
                if (store.selectedChatId() === chatId) {
                  patchState(store, {
                    selectedChatId: null,
                    currentSession: null,
                    messages: [],
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

    clearCurrentChat: () =>
      patchState(store, {
        currentSession: null,
        messages: [],
        selectedChatId: null,
      }),
  }))
);
