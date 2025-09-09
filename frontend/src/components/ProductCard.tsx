import React from 'react';
import { ShoppingCart } from 'lucide-react';
import { Product } from '../types/api';
import { Stars } from './Stars';

interface ProductCardProps {
  product: Product;
  highlightDiscount?: boolean;
  onAddToCart?: (product: Product) => void;
}

export function discountPct(price: number, compareAt?: number): number {
  if (!compareAt || compareAt <= 0 || compareAt <= price) return 0;
  return Math.round((1 - price / compareAt) * 100);
}

export function ProductCard({ product, highlightDiscount = false, onAddToCart }: ProductCardProps) {
  const pct = discountPct(product.price, product.compare_at);

  const handleAddToCart = () => {
    onAddToCart?.(product);
  };

  return (
    <article className="rounded-2xl bg-white p-4 shadow-md ring-1 ring-black/5 transition hover:shadow-lg">
      <div className="flex gap-4">
        <div className="h-28 w-28 shrink-0 overflow-hidden rounded-xl bg-neutral-100">
          <img 
            src={product.image} 
            alt={product.name} 
            className="h-full w-full object-cover" 
          />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="line-clamp-2 text-[16px] font-semibold text-neutral-900">
            {product.name}
          </h3>
          <div className="mt-1 flex items-baseline gap-2">
            <div className={`text-xl font-bold ${highlightDiscount ? "text-red-600" : "text-neutral-900"}`}>
              ¥{product.price.toFixed(2)}
            </div>
            {product.compare_at && (
              <div className="text-sm text-neutral-500 line-through">
                ¥{product.compare_at.toFixed(2)}
              </div>
            )}
            {highlightDiscount && pct > 0 && (
              <span className="ml-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-600">
                省{pct}%
              </span>
            )}
          </div>
          {product.sold && (
            <div className="text-xs text-neutral-500">已售 {product.sold}</div>
          )}
          {(product.rating || product.reviews) && (
            <div className="mt-1 flex items-center gap-1 text-neutral-700 text-xs">
              {product.rating && <Stars value={product.rating} />}
              {product.reviews && <span>({product.reviews})</span>}
            </div>
          )}
        </div>
        <button 
          onClick={handleAddToCart}
          className="ml-2 grid h-10 w-10 place-items-center self-end rounded-full bg-neutral-900 text-white shadow-md hover:bg-neutral-800 active:scale-95"
        >
          <ShoppingCart className="h-5 w-5" />
        </button>
      </div>
    </article>
  );
}
