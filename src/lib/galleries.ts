import galleriesData from '../data/galleries.json';

export type GalleryKey = keyof typeof galleriesData;

export function getGallery(key: GalleryKey | string): string[] {
  return (galleriesData as Record<string, string[]>)[key] ?? [];
}
