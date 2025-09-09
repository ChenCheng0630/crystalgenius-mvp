import { useState, useEffect } from 'react';
import { Cart, Product } from '../types/api';
import { api } from '../services/api';

export function useCart() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCart = async () => {
    try {
      setLoading(true);
      const cartData = await api.getCart();
      setCart(cartData);
      setError(null);
    } catch (err) {
      console.error('Failed to load cart:', err);
      setError('Failed to load cart');
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (product: Product, quantity = 1) => {
    try {
      const updatedCart = await api.addToCart(product.id, quantity);
      setCart(updatedCart);
      setError(null);
      return updatedCart;
    } catch (err) {
      console.error('Failed to add to cart:', err);
      setError('Failed to add to cart');
      throw err;
    }
  };

  const updateCartItem = async (itemId: string, quantity: number) => {
    try {
      const updatedCart = await api.updateCartItem(itemId, quantity);
      setCart(updatedCart);
      setError(null);
      return updatedCart;
    } catch (err) {
      console.error('Failed to update cart item:', err);
      setError('Failed to update cart item');
      throw err;
    }
  };

  const removeCartItem = async (itemId: string) => {
    try {
      const updatedCart = await api.removeCartItem(itemId);
      setCart(updatedCart);
      setError(null);
      return updatedCart;
    } catch (err) {
      console.error('Failed to remove cart item:', err);
      setError('Failed to remove cart item');
      throw err;
    }
  };

  const clearCart = async () => {
    try {
      const updatedCart = await api.clearCart();
      setCart(updatedCart);
      setError(null);
      return updatedCart;
    } catch (err) {
      console.error('Failed to clear cart:', err);
      setError('Failed to clear cart');
      throw err;
    }
  };

  useEffect(() => {
    loadCart();
  }, []);

  return {
    cart,
    loading,
    error,
    addToCart,
    updateCartItem,
    removeCartItem,
    clearCart,
    refetch: loadCart,
  };
}
