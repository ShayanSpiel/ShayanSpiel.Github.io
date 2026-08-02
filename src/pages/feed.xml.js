import { getCollection } from "astro:content";
import rss from "@astrojs/rss";
import { RSS } from "../config";

export async function GET(context) {
  const notes = await getCollection("notes");
  const sorted = notes.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());

  return rss({
    title: RSS.title,
    description: RSS.description,
    site: context.site,
    items: sorted.map((note) => ({
      title: note.data.title,
      description: note.data.description,
      pubDate: note.data.date,
      link: `/notes${note.data.permalink}`,
    })),
    stylesheet: RSS.stylesheet,
  });
}
