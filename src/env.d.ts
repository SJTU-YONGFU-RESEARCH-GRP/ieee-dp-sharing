/// <reference types="astro/client" />

declare module '*.json' {
  const value: Record<string, unknown>;
  export default value;
}
