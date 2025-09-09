import React from 'react';
import { Product } from '../types/api';
import { Stars } from './Stars';
import { discountPct } from './ProductCard';

interface ProductGridProps {
  products: Product[];
  onAddToCart?: (product: Product) => void;
}

export function ProductGrid({ products, onAddToCart }: ProductGridProps) {
  if (products.length === 0) {
    return (
      <div className="py-16 text-center text-sm text-neutral-500">
        未找到匹配结果，试试降低条件或更换关键词～
      </div>
    );
  }

  return (
    <div className="columns-2 gap-3 [column-fill:_balance]">
      {products.map((product) => (
        <div key={product.id} className="mb-3 break-inside-avoid">
          <div className="overflow-hidden rounded-2xl bg-white shadow ring-1 ring-black/5">
            <div className="relative">
              <img 
                src={product.image} 
                alt={product.name} 
                className="h-auto w-full object-cover" 
              />
              {product.compare_at && product.compare_at > product.price && (
                <span className="absolute left-2 top-2 rounded-full bg-red-600/90 px-2 py-0.5 text-xs font-bold text-white">
                  省{discountPct(product.price, product.compare_at)}%
                </span>
              )}
            </div>
            <div className="p-3">
              <div className="line-clamp-2 text-[13px] font-semibold text-neutral-900">
                {product.name}
              </div>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="text-[15px] font-bold">¥{product.price.toFixed(2)}</span>
                {product.compare_at && (
                  <span className="text-xs text-neutral-400 line-through">
                    ¥{product.compare_at.toFixed(2)}
                  </span>
                )}
              </div>
              {product.rating && (
                <div className="mt-1 flex items-center gap-1">
                  <Stars value={product.rating} />
                  {product.reviews && (
                    <span className="text-xs text-neutral-500">({product.reviews})</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
