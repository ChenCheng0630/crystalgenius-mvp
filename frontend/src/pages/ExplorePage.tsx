import React, { useState, useEffect } from 'react';
import { Send } from 'lucide-react';
import { Product, SearchAnalysis } from '../types/api';
import { api } from '../services/api';
import { ProductGrid } from '../components/ProductGrid';
import { useCart } from '../hooks/useCart';

interface ExplorePageProps {
  onBack: () => void;
}

export function ExplorePage({ onBack }: ExplorePageProps) {
  const [query, setQuery] = useState('');
  const [analysis, setAnalysis] = useState<SearchAnalysis>({
    summary: '解析：为你推荐当下人气水晶单品'
  });
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const { addToCart } = useCart();

  useEffect(() => {
    // Load initial popular products
    loadProducts();
  }, []);

  const loadProducts = async (searchQuery?: string) => {
    try {
      setLoading(true);
      if (searchQuery) {
        const response = await api.searchProducts({ q: searchQuery });
        setAnalysis(response.analysis);
        setProducts(response.products);
      } else {
        // Load popular products by default
        const response = await api.getProducts({ sort: 'popular' });
        setProducts(response.products);
      }
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoading(false);
    }
  };

  const runSearch = (text: string) => {
    if (text.trim()) {
      loadProducts(text.trim());
    } else {
      loadProducts();
    }
  };

  const handleAddToCart = async (product: Product) => {
    try {
      await addToCart(product);
      // Could show a toast notification here
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  return (
    <div className="w-full min-h-screen bg-neutral-100">
      {/* 顶部切换条 */}
      <div className="sticky top-0 z-30 w-full bg-black/90 backdrop-blur">
        <div className="mx-auto flex max-w-md items-center justify-between px-4 py-2">
          <div className="flex items-center gap-6 text-white">
            {(['guide', 'explore'] as const).map((k) => {
              const label = k === 'guide' ? '导购' : '逛逛';
              const activeTop = k === 'explore';
              return (
                <button
                  key={k}
                  onClick={() => (k === 'guide' ? onBack() : null)}
                  className={`relative pb-1.5 text-[16px] font-semibold ${
                    activeTop ? 'text-white' : 'text-white/60'
                  }`}
                >
                  {label}
                  {activeTop && (
                    <span className="absolute -bottom-0.5 left-0 right-0 mx-auto block h-0.5 w-9 rounded bg-white" />
                  )}
                </button>
              );
            })}
          </div>
          <div className="h-6 w-6" />
        </div>
      </div>

      {/* 解析与搜索条 */}
      <div className="mx-auto max-w-md px-4 pt-3">
        <div className="rounded-2xl bg-black text-white px-4 py-3 shadow">
          <div className="text-xs text-white/70">搜索/筛选解析</div>
          <div className="mt-1 text-sm leading-relaxed">{analysis.summary}</div>
        </div>

        <div className="mt-3 flex items-center gap-2 rounded-full bg-white p-3 shadow ring-1 ring-black/5">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runSearch(query)}
            placeholder="自然语言搜索：想要300以内、红色、能量手串…"
            className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-neutral-400"
          />
          <button
            onClick={() => runSearch(query)}
            className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white active:scale-95"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* 产品网格 */}
      <div className="mx-auto max-w-md px-4 py-4 pb-16">
        {loading ? (
          <div className="py-16 text-center text-sm text-neutral-500">搜索中...</div>
        ) : (
          <ProductGrid products={products} onAddToCart={handleAddToCart} />
        )}
      </div>
    </div>
  );
}
