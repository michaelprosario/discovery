/**
 * API Configuration Service
 * Manages API base URL and common configuration
 */

import { Injectable } from '@angular/core';

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiConfigService {
  private config: ApiConfig = {
    baseUrl: this.getDefaultBaseUrl(),
    timeout: 30000
  };

  /**
   * Get the current API configuration
   */
  getConfig(): ApiConfig {
    return { ...this.config };
  }

  /**
   * Get the API base URL
   */
  getBaseUrl(): string {
    return this.config.baseUrl;
  }

  /**
   * Set the API base URL
   */
  setBaseUrl(url: string): void {
    this.config.baseUrl = url;
  }

  /**
   * Get the request timeout in milliseconds
   */
  getTimeout(): number {
    return this.config.timeout;
  }

  /**
   * Set the request timeout in milliseconds
   */
  setTimeout(timeout: number): void {
    this.config.timeout = timeout;
  }

  /**
   * Get default base URL based on environment
   */
  private getDefaultBaseUrl(): string {
    // Check if running in development mode
    if (typeof window !== 'undefined' && window.location) {
      const hostname = window.location.hostname;
      const port = window.location.port;
      
      // If running on localhost with a different port, assume API is on 8000
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return `http://${hostname}:8000`;
      }
    }
    
    // Default to relative path for production
    return '';
  }
}
