/// <reference types="vite/client" />

declare interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_MODE?: "mock" | "live";
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv;
}
