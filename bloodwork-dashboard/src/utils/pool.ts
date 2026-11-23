// Run `worker` over `items` with at most `limit` running at the same time.
// The worker is expected to handle its own errors; a throw would stop that lane.
export async function runPool<T>(
  items: T[],
  limit: number,
  worker: (item: T) => Promise<void>,
): Promise<void> {
  let next = 0

  async function lane() {
    while (next < items.length) {
      const item = items[next++]!
      await worker(item)
    }
  }

  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, lane))
}
