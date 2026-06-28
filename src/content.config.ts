import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    date: z.coerce.date(),
    permalink: z.string(),
    galleryKey: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
