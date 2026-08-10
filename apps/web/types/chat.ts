export interface Citation {
  id: string;
  entity_type: 'venture' | 'project' | 'person' | 'interaction' | 'memory' | 'document' | 'idea';
  title: string;
  uri?: string;
  snippet?: string;
}

export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageStatus = 'optimistic' | 'thinking' | 'streaming' | 'completed' | 'error';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  status?: MessageStatus;
  isThinking?: boolean;
  thinkingText?: string;
  citations?: Citation[];
  error?: string;
}

export interface UseChatOptions {
  api?: string; // Endpoint URL, defaults to '/api/v1/ai/search' or backend RAG endpoint
  initialMessages?: ChatMessage[];
  onFinish?: (message: ChatMessage) => void;
  onError?: (error: Error) => void;
  headers?: Record<string, string>;
  body?: Record<string, any>;
}

export interface UseChatHelpers {
  messages: ChatMessage[];
  input: string;
  setInput: (value: string) => void;
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  handleSubmit: (e?: React.FormEvent<HTMLFormElement>) => Promise<void>;
  sendMessage: (content?: string) => Promise<void>;
  isLoading: boolean;
  isThinking: boolean;
  stop: () => void;
  reload: () => Promise<void>;
  clearMessages: () => void;
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  error: Error | null;
}
