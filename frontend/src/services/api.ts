import {
  AssistantProfile,
  Product,
  ProductListResponse,
  SearchResponse,
  ChatResponse,
  Cart,
  CurationsListResponse,
  CurationResponse,
  ParentCategory,
  Category,
  CheckoutSession,
  CheckoutStatus,
  ChatMessage,
} from '../types/api';

const API_BASE = '/api/v1';

class ApiError extends Error {
  constructor(public code: string, message: string, public details?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for session management
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        throw new ApiError('network_error', `HTTP ${response.status}`);
      }

      if (errorData.error) {
        throw new ApiError(
          errorData.error.code,
          errorData.error.message,
          errorData.error.details
        );
      }

      throw new ApiError('unknown_error', `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Assistant & Curations
  async getAssistantProfile(): Promise<AssistantProfile> {
    return this.request('/assistant/profile');
  }

  async getCurations(): Promise<CurationsListResponse> {
    return this.request('/curations');
  }

  async getCuration(slug: string, page = 1, pageSize = 20): Promise<CurationResponse> {
    return this.request(`/curations/${slug}?page=${page}&page_size=${pageSize}`);
  }

  // Products & Search
  async getProducts(params: {
    q?: string;
    parent_category_id?: number;
    color?: string[];
    material?: string[];
    category_name?: string[];
    category_id?: number[];
    min_price?: number;
    max_price?: number;
    sort?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<ProductListResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(`${key}[]`, v.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    return this.request(`/products?${searchParams}`);
  }

  async getProduct(id: number): Promise<Product> {
    return this.request(`/products/${id}`);
  }

  async searchProducts(params: {
    q: string;
    parent_category_id?: number;
    color?: string[];
    material?: string[];
    category_name?: string[];
    category_id?: number[];
    min_price?: number;
    max_price?: number;
    sort?: string;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(`${key}[]`, v.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    return this.request(`/products/search?${searchParams}`);
  }

  async getParentCategories(): Promise<{ parent_categories: ParentCategory[] }> {
    return this.request('/parent-categories');
  }

  async getCategories(parentId?: number): Promise<{ categories: Category[] }> {
    const params = parentId ? `?parent_id=${parentId}` : '';
    return this.request(`/categories${params}`);
  }

  // Chat
  async createChatSession(): Promise<{ session_id: string }> {
    return this.request('/chat/sessions', { method: 'POST' });
  }

  async getChatMessages(): Promise<{ messages: ChatMessage[] }> {
    return this.request('/chat/messages');
  }

  async sendChatMessage(message: string): Promise<ChatResponse> {
    return this.request('/chat/messages', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  // SSE Chat Stream
  createChatStream(message: string): EventSource {
    const params = new URLSearchParams({ message });
    return new EventSource(`${API_BASE}/chat/stream?${params}`, {
      withCredentials: true,
    });
  }

  // Cart
  async getCart(): Promise<Cart> {
    return this.request('/cart');
  }

  async addToCart(productId: number, quantity = 1): Promise<Cart> {
    return this.request('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  }

  async updateCartItem(itemId: string, quantity: number): Promise<Cart> {
    return this.request(`/cart/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    });
  }

  async removeCartItem(itemId: string): Promise<Cart> {
    return this.request(`/cart/items/${itemId}`, { method: 'DELETE' });
  }

  async clearCart(): Promise<Cart> {
    return this.request('/cart', { method: 'DELETE' });
  }

  // Checkout
  async createCheckoutSession(returnUrl: string, cancelUrl: string): Promise<CheckoutSession> {
    return this.request('/checkout/sessions', {
      method: 'POST',
      body: JSON.stringify({ return_url: returnUrl, cancel_url: cancelUrl }),
    });
  }

  async getCheckoutStatus(checkoutId: string): Promise<CheckoutStatus> {
    return this.request(`/checkout/sessions/${checkoutId}`);
  }

  // Telemetry
  async sendEvent(event: string, payload: any = {}): Promise<{ ok: boolean }> {
    return this.request('/events', {
      method: 'POST',
      body: JSON.stringify({ event, payload }),
    });
  }
}

export const api = new ApiClient();
export { ApiError };
