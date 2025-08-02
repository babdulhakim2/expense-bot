/**
 * Currency utilities for consistent currency formatting across the app
 */

export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: "$",
  EUR: "€", 
  GBP: "£",
  CAD: "C$",
  AUD: "A$",
  JPY: "¥",
  CHF: "CHF",
  SEK: "kr",
  NOK: "kr",
  DKK: "kr",
};

export const SUPPORTED_CURRENCIES = [
  { code: "USD", name: "US Dollar", symbol: "$" },
  { code: "EUR", name: "Euro", symbol: "€" },
  { code: "GBP", name: "British Pound", symbol: "£" },
  { code: "CAD", name: "Canadian Dollar", symbol: "C$" },
  { code: "AUD", name: "Australian Dollar", symbol: "A$" },
  { code: "JPY", name: "Japanese Yen", symbol: "¥" },
  { code: "CHF", name: "Swiss Franc", symbol: "CHF" },
];

/**
 * Get currency symbol for a given currency code
 */
export function getCurrencySymbol(currencyCode?: string): string {
  if (!currencyCode) return "$"; // Default to USD
  return CURRENCY_SYMBOLS[currencyCode] || currencyCode;
}

/**
 * Format amount with proper currency symbol
 */
export function formatCurrency(amount: number, currencyCode?: string): string {
  const symbol = getCurrencySymbol(currencyCode);
  return `${symbol}${amount.toFixed(2)}`;
}

/**
 * Get currency info by code
 */
export function getCurrencyInfo(currencyCode?: string) {
  return SUPPORTED_CURRENCIES.find(c => c.code === currencyCode) || SUPPORTED_CURRENCIES[0];
}