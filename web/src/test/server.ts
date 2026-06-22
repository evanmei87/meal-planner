import { setupServer } from 'msw/node'

/**
 * Shared MSW server instance. Callers must manage the lifecycle:
 *   beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
 *   afterEach(() => server.resetHandlers())
 *   afterAll(() => server.close())
 *
 * Note: do NOT call server.listen() in a global setup file alongside this
 * instance — MSW v2's shared FetchInterceptor singleton causes conflicts
 * when two servers are active in the same Vitest worker.
 */
export const server = setupServer()
