/** Prefix internal paths with Astro's base (needed for github.io project preview). */
export function withBase(path: string): string {
  if (!path || path.startsWith('http')) return path;

  const normalized = path.startsWith('/') ? path : `/${path}`;
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  if (!base || base === '/') return normalized;

  return `${base}${normalized}`;
}

/** Strip the configured base from the current pathname for route matching. */
export function stripBase(pathname: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  if (!base || base === '/') return pathname;
  if (pathname === base) return '/';
  if (pathname.startsWith(`${base}/`)) return pathname.slice(base.length);
  return pathname;
}
