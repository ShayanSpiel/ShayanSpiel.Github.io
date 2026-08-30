import { defineCollection, z } from "astro:content";

const noteSchema = z.object({
  title: z.string(),
  description: z.string(),
  date: z.string().transform((str) => new Date(str)),
  permalink: z.string(),
  category: z.enum(["journey", "ai-agents"]).default("journey"),
  tags: z.array(z.string()).default([]),
  image: z.string().optional(),
  faq: z.array(z.object({ q: z.string(), a: z.string() })).optional(),
});

const notes = defineCollection({
  type: "content",
  schema: noteSchema,
});

const notesFa = defineCollection({
  type: "content",
  schema: noteSchema,
});

export const collections = { notes, notesFa };
