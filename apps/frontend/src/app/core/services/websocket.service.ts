import { Injectable, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { share } from 'rxjs/operators';

export interface WebSocketMessage {
  type: string;
  timestamp?: string; // ISO datetime string
  [key: string]: unknown;
}

export interface ConnectionEvent extends WebSocketMessage {
  type: 'connection';
  status: 'connected' | 'disconnected' | 'error';
  message?: string;
}

@Injectable({
  providedIn: 'root',
})
export class WebSocketService implements OnDestroy {
  private socket: WebSocket | null = null;
  private messagesSubject = new Subject<WebSocketMessage>();
  private connectionSubject = new Subject<ConnectionEvent>();

  private reconnectInterval = 5000; // 5 seconds
  private maxReconnectAttempts = 10;
  private reconnectAttempts = 0;
  private intentionalDisconnect = false;

  // Observable streams
  messages$ = this.messagesSubject.asObservable().pipe(share());
  connection$ = this.connectionSubject.asObservable().pipe(share());

  connect(): void {
    // Check if already connected or connecting
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this.intentionalDisconnect = false;
    this.createConnection();
  }

  private createConnection(): void {
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.connectionSubject.next({
        type: 'connection',
        status: 'error',
        message: 'No authentication token',
      });
      return;
    }

    // Use proxy path in development, full URL in production
    let wsUrl: string;
    if (window.location.port === '4200') {
      // Development mode - connect directly to backend
      wsUrl = `ws://localhost:8000/ws?token=${token}`;
    } else {
      // Production mode - use full URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/ws?token=${token}`;
    }

    try {
      this.socket = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      this.handleError(error);
    }
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.connectionSubject.next({
        type: 'connection',
        status: 'connected',
        message: 'WebSocket connected successfully',
      });

      // Send periodic ping to keep connection alive
      this.startHeartbeat();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.messagesSubject.next(data);
      } catch {
        // Ignore parsing errors
      }
    };

    this.socket.onerror = (error) => {
      this.handleError(error);
    };

    this.socket.onclose = (event) => {
      this.stopHeartbeat();

      this.connectionSubject.next({
        type: 'connection',
        status: 'disconnected',
        message: `Disconnected: ${event.reason || 'Connection lost'}`,
      });

      // Attempt reconnection if not intentional
      if (
        !this.intentionalDisconnect &&
        this.reconnectAttempts < this.maxReconnectAttempts
      ) {
        this.scheduleReconnect();
      }
    };
  }

  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    console.log(
      `Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
    );

    setTimeout(() => {
      if (!this.intentionalDisconnect) {
        this.createConnection();
      }
    }, this.reconnectInterval);
  }

  private handleError(error: Event | Error | unknown): void {
    this.connectionSubject.next({
      type: 'connection',
      status: 'error',
      message: (error as Error).message || 'WebSocket error occurred',
    });
  }

  send(message: WebSocketMessage): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }


  disconnect(): void {
    this.intentionalDisconnect = true;
    this.stopHeartbeat();

    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  ngOnDestroy(): void {
    this.disconnect();
    this.messagesSubject.complete();
    this.connectionSubject.complete();
  }
}
