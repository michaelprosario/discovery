/**
 * API Configuration Service
 * Manages API base URL and common configuration
 */

import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiConfigService {
  private config: ApiConfig = {
    baseUrl: environment.apiUrl,
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
}
