import galleriesData from '../data/galleries.json';
import { withBase } from './base';

export type GalleryKey = keyof typeof galleriesData;

export function getGallery(key: GalleryKey | string): string[] {
  const images = (galleriesData as Record<string, string[]>)[key] ?? [];
  return images.map(withBase);
}
