import React, { useState, useEffect, useRef } from 'react';
import { Send } from 'lucide-react';
import { ChatMessage, Product, AssistantProfile } from '../types/api';
import { api } from '../services/api';
import { ProductCard } from '../components/ProductCard';
import { useCart } from '../hooks/useCart';

interface ChatPageProps {
  onBack: () => void;
  prefill?: string;
}

export function ChatPage({ onBack, prefill = '' }: ChatPageProps) {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([]);
  const [input, setInput] = useState('');
  const [caption, setCaption] = useState<string>('');
  const [showCaption, setShowCaption] = useState(false);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Product[]>([]);
  const [profile, setProfile] = useState<AssistantProfile | null>(null);
  const { addToCart } = useCart();

  // Store background image URL
  const bg = "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop";

  useEffect(() => {
    loadProfile();
    if (prefill) {
      setInput(prefill);
      setTimeout(() => send(), 50);
    }
  }, [prefill]);

  const loadProfile = async () => {
    try {
      const profileData = await api.getAssistantProfile();
      setProfile(profileData);
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  // 字幕：出现并在 2.5s 后淡出
  const pushCaption = (text: string) => {
    setCaption(text);
    setShowCaption(true);
    setTimeout(() => setShowCaption(false), 2500);
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: 'user', text }]);
    setInput('');
    setLoading(true);
    setSuggestions([]);

    try {
      // Try streaming first, fallback to regular API
      if (typeof EventSource !== 'undefined') {
        await sendStreamingMessage(text);
      } else {
        await sendRegularMessage(text);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages((m) => [...m, { role: 'assistant', text: '抱歉，我遇到了一些问题。请稍后再试。' }]);
    } finally {
      setLoading(false);
    }
  };

  const sendStreamingMessage = async (text: string) => {
    return new Promise<void>((resolve, reject) => {
      const eventSource = api.createChatStream(text);
      let assistantMessage = '';

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (event.type === 'assistant_message') {
            assistantMessage += data.content;
            setMessages((m) => {
              const newMessages = [...m];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage && lastMessage.role === 'assistant') {
                lastMessage.text = assistantMessage;
              } else {
                newMessages.push({ role: 'assistant', text: assistantMessage });
              }
              return newMessages;
            });
          } else if (event.type === 'product_suggestions') {
            setSuggestions(data.products || []);
            if (data.reason) {
              pushCaption(data.reason);
            }
          } else if (event.type === 'done') {
            eventSource.close();
            resolve();
          }
        } catch (error) {
          console.error('Error parsing SSE data:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();
        // Fallback to regular API
        sendRegularMessage(text).then(resolve).catch(reject);
      };

      // Timeout fallback
      setTimeout(() => {
        if (eventSource.readyState !== EventSource.CLOSED) {
          eventSource.close();
          sendRegularMessage(text).then(resolve).catch(reject);
        }
      }, 30000);
    });
  };

  const sendRegularMessage = async (text: string) => {
    const response = await api.sendChatMessage(text);
    
    // Add assistant message
    const assistantMessage = response.messages.find(m => m.role === 'assistant');
    if (assistantMessage) {
      setMessages((m) => [...m, { role: 'assistant', text: assistantMessage.content }]);
      pushCaption(assistantMessage.content);
    }

    // Add product suggestions
    if (response.suggestions && response.suggestions.products.length > 0) {
      setSuggestions(response.suggestions.products);
      if (response.suggestions.reason) {
        pushCaption(response.suggestions.reason);
      }
    }
  };

  const handleAddToCart = async (product: Product) => {
    try {
      await addToCart(product);
      pushCaption(`已添加 ${product.name} 到购物车`);
    } catch (error) {
      console.error('Failed to add to cart:', error);
      pushCaption('添加到购物车失败');
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-black text-white">
      {/* 背景图 */}
      <img src={bg} alt="store" className="absolute inset-0 h-full w-full object-cover opacity-80" />

      {/* 返回 */}
      <div className="absolute left-3 top-3 z-20">
        <button
          onClick={onBack}
          className="rounded-full bg-white/20 px-3 py-1 text-sm backdrop-blur"
        >
          返回
        </button>
      </div>

      {/* 顶部小窗（示意） */}
      <div className="absolute left-3 top-16 z-10 overflow-hidden rounded-xl ring-2 ring-white/60">
        {profile && (
          <img src={profile.avatar} className="h-20 w-16 object-cover" alt="Assistant" />
        )}
      </div>

      {/* 字幕 */}
      <div
        className={`pointer-events-none absolute left-5 right-5 top-36 z-10 transition-opacity ${
          showCaption ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="mx-auto max-w-xs rounded-2xl bg-black/60 px-4 py-2 text-center text-base leading-snug shadow-lg">
          {caption}
        </div>
      </div>

      {/* 聊天消息区 */}
      <div className="absolute inset-x-0 bottom-28 top-24 z-0 overflow-y-auto px-4">
        <div className="mx-auto max-w-md space-y-2">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`${
                  m.role === 'user'
                    ? 'bg-white text-neutral-900'
                    : 'bg-neutral-900/80 text-white'
                } max-w-[75%] rounded-2xl px-3 py-2 text-sm shadow`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-neutral-900/80 text-white max-w-[75%] rounded-2xl px-3 py-2 text-sm shadow">
                正在思考...
              </div>
            </div>
          )}
        </div>

        {/* Product suggestions */}
        {suggestions.length > 0 && (
          <div className="mx-auto max-w-md mt-4 space-y-3">
            <div className="text-center text-sm text-white/80">为您推荐</div>
            {suggestions.slice(0, 3).map((product) => (
              <div key={product.id} className="bg-white/90 rounded-2xl p-2">
                <ProductCard
                  product={product}
                  onAddToCart={handleAddToCart}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部输入区 */}
      <div className="absolute bottom-4 left-0 right-0 z-20 mx-auto max-w-md px-4">
        <div className="flex items-center gap-2 rounded-full bg-white p-3 text-neutral-900 shadow-xl ring-1 ring-black/5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-neutral-400"
            placeholder="和导购说点什么…"
            disabled={loading}
          />
          <button
            onClick={send}
            disabled={loading}
            className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white active:scale-95 disabled:opacity-50"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
