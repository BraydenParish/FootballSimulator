declare module "msw" {
  export const rest: {
    get: (path: string, resolver: (...args: any[]) => any) => any;
    post: (path: string, resolver: (...args: any[]) => any) => any;
  };
}

declare module "msw/browser" {
  export interface SetupWorkerApi {
    start(options?: { quiet?: boolean }): Promise<void>;
    stop(): Promise<void>;
    resetHandlers(...handlers: any[]): void;
    use(...handlers: any[]): void;
  }
  export function setupWorker(...handlers: any[]): SetupWorkerApi;
}
