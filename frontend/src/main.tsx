import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import type { TestSeed } from "./types/testSeed";

declare global {
  interface Window {
    __E2E_SEED__?: TestSeed;
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

async function bootstrap() {
  if (import.meta.env.DEV && window.__E2E_SEED__) {
    const { startWorker } = await import("./mocks/e2eWorker");
    await startWorker(window.__E2E_SEED__);
  }

  ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>
  );
}

void bootstrap();
