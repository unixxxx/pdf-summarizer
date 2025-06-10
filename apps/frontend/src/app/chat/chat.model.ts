// DTO interfaces for API responses
export interface ChatDto {
  id: string;
  document_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  document_filename?: string;
  last_message?: string;
  message_count?: number;
}

export interface ChatMessageDto {
  id: string;
  chat_id: string;
  role: string;
  content: string;
  created_at: string;
  message_metadata?: MessageMetadata;
}

/**
 * Domain model for Chat entity
 */
export class Chat {
  constructor(
    public readonly id: string,
    public readonly documentId: string,
    public readonly userId: string,
    public readonly title: string,
    public readonly createdAt: Date,
    public readonly updatedAt: Date,
    public readonly documentFilename?: string,
    public readonly lastMessage?: string,
    public readonly messageCount = 0
  ) {}

  /**
   * Check if chat is active (updated within 24 hours)
   */
  get isActive(): boolean {
    const dayInMs = 24 * 60 * 60 * 1000;
    return Date.now() - this.updatedAt.getTime() < dayInMs;
  }

  /**
   * Get display title
   */
  get displayTitle(): string {
    return this.title || `Chat with ${this.documentFilename || 'Document'}`;
  }

  /**
   * Create from API response
   */
  static fromDto(dto: ChatDto): Chat {
    return new Chat(
      dto.id,
      dto.document_id,
      dto.user_id,
      dto.title,
      new Date(dto.created_at),
      new Date(dto.updated_at),
      dto.document_filename,
      dto.last_message,
      dto.message_count || 0
    );
  }
}

/**
 * Domain model for Chat Message
 */
export class ChatMessage {
  constructor(
    public readonly id: string,
    public readonly chatId: string,
    public readonly role: MessageRole,
    public readonly content: string,
    public readonly createdAt: Date,
    public readonly metadata?: MessageMetadata
  ) {}

  /**
   * Check if message is from user
   */
  get isUserMessage(): boolean {
    return this.role === MessageRole.USER;
  }

  /**
   * Check if message is from assistant
   */
  get isAssistantMessage(): boolean {
    return this.role === MessageRole.ASSISTANT;
  }

  /**
   * Get chunks used for this message (if AI response)
   */
  get chunksUsed(): number {
    return this.metadata?.chunks_used?.length || 0;
  }

  /**
   * Create from API response
   */
  static fromDto(dto: ChatMessageDto): ChatMessage {
    return new ChatMessage(
      dto.id,
      dto.chat_id,
      dto.role as MessageRole,
      dto.content,
      new Date(dto.created_at),
      dto.message_metadata
    );
  }
}

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

export interface MessageMetadata {
  chunks_used?: Array<{
    chunk_id: string;
    similarity: number;
    chunk_index: number;
  }>;
  model?: string;
}
