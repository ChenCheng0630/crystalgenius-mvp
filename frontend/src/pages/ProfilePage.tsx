import React, { useState, useEffect, useRef } from 'react';
import { Trophy, Send, MessageCircle, Tag } from 'lucide-react';
import { AssistantProfile, Product } from '../types/api';
import { api } from '../services/api';
import { ProductCard } from '../components/ProductCard';
import { useCart } from '../hooks/useCart';

interface ProfilePageProps {
  onStartChat: () => void;
  onExplore: () => void;
}

export function ProfilePage({ onStartChat, onExplore }: ProfilePageProps) {
  const [profile, setProfile] = useState<AssistantProfile | null>(null);
  const [activeTab, setActiveTab] = useState<'flash' | 'weekly'>('flash');
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [prefillMsg, setPrefillMsg] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const { addToCart } = useCart();

  const TAB_LABELS = ['她的秒杀商品', '她的本周推荐'] as const;

  useEffect(() => {
    loadProfile();
    loadCuration('flash-deals');
  }, []);

  const loadProfile = async () => {
    try {
      const profileData = await api.getAssistantProfile();
      setProfile(profileData);
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const loadCuration = async (slug: string) => {
    try {
      setLoading(true);
      const response = await api.getCuration(slug);
      setProducts(response.curation.products);
    } catch (error) {
      console.error('Failed to load curation:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab: 'flash' | 'weekly') => {
    setActiveTab(tab);
    const slug = tab === 'flash' ? 'flash-deals' : 'weekly-picks';
    loadCuration(slug);
  };

  const handleSendFromHome = () => {
    const text = inputRef.current?.value?.trim();
    if (text) {
      setPrefillMsg(text);
      onStartChat();
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

  if (!profile) {
    return (
      <div className="w-full min-h-screen bg-neutral-100 flex items-center justify-center">
        <div className="text-neutral-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen bg-neutral-100 text-neutral-900">
      {/* 顶部切换条 */}
      <div className="sticky top-0 z-30 w-full bg-black/90 backdrop-blur">
        <div className="mx-auto flex max-w-md items-center justify-between px-4 py-2">
          <div className="flex items-center gap-6 text-white">
            {(['guide', 'explore'] as const).map((k) => {
              const label = k === 'guide' ? '导购' : '逛逛';
              const activeTop = k === 'guide';
              return (
                <button
                  key={k}
                  onClick={() => k === 'explore' ? onExplore() : null}
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

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-neutral-900" />
        <div className="absolute inset-x-0 -top-40 h-[28rem] bg-gradient-to-b from-neutral-800 via-neutral-900 to-neutral-900 opacity-90" />

        <div className="relative z-10 mx-auto flex max-w-md flex-col items-center px-4 pt-10 pb-6">
          <div className="mx-auto h-36 w-36 overflow-hidden rounded-full border-4 border-neutral-800 shadow-2xl ring-8 ring-black/20">
            <img src={profile.avatar} alt="导购头像" className="h-full w-full object-cover" />
          </div>
          <h1 className="mt-5 text-center text-3xl font-bold text-white">{profile.name}</h1>
          <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-white text-sm backdrop-blur ring-1 ring-white/15">
            <Trophy className="h-4 w-4 text-amber-300" />
            <span>本月最佳AI购物导购</span>
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
            {profile.domains.map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm text-white"
              >
                {chip}
              </span>
            ))}
          </div>

          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {profile.styles.map((style) => (
              <span
                key={style}
                className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-sm text-white/80"
              >
                {style}
              </span>
            ))}
          </div>

          <p className="mt-4 max-w-md text-center text-white/90">{profile.intro_short}</p>

          <div className="mt-5 grid w-full max-w-md grid-cols-3 gap-3 text-center text-white">
            <div>
              <div className="text-xs text-white/70">月成交量</div>
              <div className="mt-1 text-lg font-bold">{profile.stats.monthly_sales}</div>
            </div>
            <div>
              <div className="text-xs text-white/70">GMV</div>
              <div className="mt-1 text-lg font-bold">{profile.stats.gmv}</div>
            </div>
            <div>
              <div className="text-xs text-white/70">好评率</div>
              <div className="mt-1 text-lg font-bold">{profile.stats.positive_rate}</div>
            </div>
          </div>

          <button
            onClick={onStartChat}
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-white/90 px-5 py-2 text-[15px] font-semibold text-neutral-900 shadow-lg backdrop-blur transition hover:bg-white"
          >
            <MessageCircle className="h-5 w-5" /> 点击进行对话
          </button>
        </div>
      </section>

      {/* 商品区内 Tabs */}
      <div className="sticky top-[48px] z-20 mx-auto w-full max-w-md bg-neutral-100/95 px-4 pt-3 backdrop-blur">
        <div className="flex gap-6 border-b border-neutral-200 pb-1">
          {TAB_LABELS.map((label, idx) => {
            const isActive = (idx === 0 && activeTab === 'flash') || (idx === 1 && activeTab === 'weekly');
            return (
              <button
                key={label}
                onClick={() => handleTabChange(idx === 0 ? 'flash' : 'weekly')}
                className={`relative pb-2 text-[20px] font-bold transition-colors ${
                  isActive ? 'text-neutral-900' : 'text-neutral-400'
                }`}
              >
                {label}
                {isActive && (
                  <span className="absolute -bottom-[3px] left-0 right-0 mx-auto block h-1 w-[56px] rounded-full bg-neutral-900" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Products */}
      <div className="mx-auto max-w-md space-y-4 px-4 py-4 pb-28">
        {loading ? (
          <div className="py-8 text-center text-neutral-500">加载中...</div>
        ) : (
          products.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              highlightDiscount={activeTab === 'flash'}
              onAddToCart={handleAddToCart}
            />
          ))
        )}
      </div>

      {/* Floating composer */}
      <div className="fixed bottom-4 left-0 right-0 z-30 mx-auto max-w-md px-4">
        <div className="flex items-center gap-2 rounded-full bg-white p-3 shadow-xl ring-1 ring-black/5">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white">
            <Tag className="h-5 w-5" />
          </div>
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-neutral-400"
            placeholder="和导购说：想要本周推荐里更基础百搭的款…"
          />
          <button
            onClick={handleSendFromHome}
            className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white active:scale-95"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
