import { useState, useEffect, useCallback } from 'react';
import { predictionApi } from '../services/api';
import { useDebounce } from './useDebounce';

interface SearchResult {
  players: string[];
  total_matches: number;
}

export function usePlayerSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalMatches, setTotalMatches] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [searchCache, setSearchCache] = useState<Map<string, SearchResult>>(new Map());

  // Faster debounce for better UX
  const debouncedSearchQuery = useDebounce(searchQuery, 150);

  const searchPlayers = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      setTotalMatches(0);
      setLoading(false); // Ensure loading is false for short queries
      return;
    }

    // Check cache first
    const cacheKey = query.toLowerCase();
    const cachedResult = searchCache.get(cacheKey);
    
    if (cachedResult) {
      setSearchResults(cachedResult.players);
      setTotalMatches(cachedResult.total_matches);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const response = await predictionApi.searchPlayers(query, 100);
      
      // Cache successful results
      if (response.players.length > 0) {
        setSearchCache(prev => {
          const newCache = new Map(prev);
          newCache.set(cacheKey, response);
          
          // Limit cache size to prevent memory issues
          if (newCache.size > 50) {
            const firstKey = newCache.keys().next().value;
            newCache.delete(firstKey);
          }
          
          return newCache;
        });
      }
      
      setSearchResults(response.players);
      setTotalMatches(response.total_matches);
    } catch (error) {
      console.error('Failed to search players:', error);
      setSearchResults([]);
      setTotalMatches(0);
    } finally {
      setLoading(false);
    }
  }, [searchCache]);

  // Track when user is typing vs when we're searching
  useEffect(() => {
    if (searchQuery !== debouncedSearchQuery && searchQuery.length >= 2) {
      setIsTyping(true);
    } else {
      setIsTyping(false);
    }
  }, [searchQuery, debouncedSearchQuery]);

  useEffect(() => {
    searchPlayers(debouncedSearchQuery);
  }, [debouncedSearchQuery, searchPlayers]);

  return {
    searchQuery,
    setSearchQuery,
    searchResults,
    loading: loading || isTyping,
    totalMatches,
  };
}