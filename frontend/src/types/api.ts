// API Types matching backend specification

export interface Product {
  id: number;
  reference_id: string;
  name: string;
  price: number;
  currency: string;
  compare_at?: number;
  image: string;
  extra_images?: string[];
  description?: string;
  categories?: Category[];
  sold?: string;
  rating?: number;
  reviews?: number;
  tags?: string[];
}

export interface Category {
  id: number;
  reference_id: number;
  category_name: string;
  parent_id: number;
  color?: string;
  material?: string;
  image?: string;
}

export interface ParentCategory {
  id: number;
  reference_id: number;
  name: string;
  image?: string;
}

export interface AssistantProfile {
  name: string;
  avatar: string;
  intro_short: string;
  domains: string[];
  styles: string[];
  stats: {
    monthly_sales: string;
    gmv: string;
    positive_rate: string;
  };
  ctas?: Array<{
    label: string;
    action: "chat" | "explore";
  }>;
}

export interface Curation {
  slug: string;
  title: string;
  description?: string;
  products: Product[];
}

export interface SearchAnalysis {
  summary: string;
  colors?: string[];
  materials?: string[];
  category_names?: string[];
  price_range?: {
    min?: number;
    max?: number;
  };
}

export interface Cart {
  id: string;
  items: CartItem[];
  totals: {
    subtotal: number;
    currency: string;
  };
}

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  unit_price: number;
  currency: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ProductSuggestions {
  products: Product[];
  reason?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
}

export interface ProductListResponse {
  products: Product[];
  meta: PaginationMeta;
}

export interface SearchResponse {
  analysis: SearchAnalysis;
  products: Product[];
  meta: PaginationMeta;
}

export interface ChatResponse {
  messages: ChatMessage[];
  suggestions?: ProductSuggestions;
}

export interface CurationResponse {
  curation: Curation;
  meta: PaginationMeta;
}

export interface CurationsListResponse {
  curations: Array<{
    slug: string;
    title: string;
  }>;
}

export interface CheckoutSession {
  checkout_id: string;
  checkout_url: string;
  expires_at: string;
}

export interface CheckoutStatus {
  status: "pending" | "paid" | "canceled" | "expired";
  order_id?: string;
}
