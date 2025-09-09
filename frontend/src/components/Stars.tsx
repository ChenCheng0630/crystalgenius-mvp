import React from 'react';
import { Star } from 'lucide-react';

interface StarsProps {
  value?: number;
  max?: number;
}

export function Stars({ value = 5, max = 5 }: StarsProps) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: max }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${
            i < value
              ? "fill-current text-yellow-500"
              : "fill-transparent text-gray-300"
          }`}
        />
      ))}
    </div>
  );
}
