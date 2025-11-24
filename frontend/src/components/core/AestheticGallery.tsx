import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import type { GalleryItem } from "../../types";
import { api } from "../../lib/api";
import { Skeleton } from "../ui/Skeleton";

const PAGE_SIZE = 9;

export function AestheticGallery() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const observerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchGallery(nextPage: number) {
      try {
        setIsLoading(true);
        const data = await api.listGallery(nextPage, PAGE_SIZE);
        if (cancelled) return;
        setItems((prev) => [...prev, ...data.items]);
      } catch (fetchError) {
        console.error(fetchError);
        if (!cancelled) {
          setError(fetchError instanceof Error ? fetchError.message : "加载失败");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchGallery(page);
    return () => {
      cancelled = true;
    };
  }, [page]);

  useEffect(() => {
    const node = observerRef.current;
    if (!node || items.length === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !isLoading) {
            observer.unobserve(entry.target);
            setPage((prev) => prev + 1);
          }
        });
      },
      {
        rootMargin: "200px",
      },
    );

    observer.observe(node);
    return () => {
      observer.disconnect();
    };
  }, [isLoading, items.length]);

  const groupedItems = useMemo(() => {
    const columns = [[], [], []] as GalleryItem[][];
    items.forEach((item, index) => {
      columns[index % 3].push(item);
    });
    return columns;
  }, [items]);

  return (
    <div className="flex max-h-[520px] flex-col gap-4 overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-200 backdrop-blur-xl">
      <div className="flex items-baseline justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">美学作品展示</h2>
          <p className="mt-1 text-sm text-slate-400">探索社区精选作品，实时刷新灵感。</p>
        </div>
        <span className="rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs uppercase tracking-[0.3em] text-slate-400">
          Gallery
        </span>
      </div>

      <div className="relative flex-1 overflow-y-auto pr-1">
        <div className="grid gap-4 lg:grid-cols-3">
          {groupedItems.map((column, columnIndex) => (
            <div key={`col-${columnIndex}`} className="flex flex-col gap-4">
              {column.map((item) => (
                <motion.article
                  key={item.id}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                  className="overflow-hidden rounded-3xl border border-white/10 bg-black/30"
                >
                  <div className="relative aspect-[4/5] overflow-hidden">
                    <img
                      src={item.image_url}
                      alt={item.title}
                      loading="lazy"
                      className="h-full w-full object-cover"
                    />
                    <div className="absolute left-3 top-3 rounded-full bg-black/60 px-3 py-1 text-xs text-white/80">
                      {item.author}
                    </div>
                  </div>
                  <div className="space-y-3 px-4 py-4 text-sm text-slate-200">
                    <h3 className="text-base font-semibold text-white">{item.title}</h3>
                    <div className="flex flex-wrap gap-2 text-xs text-slate-400">
                      <span>❤ {item.likes}</span>
                      <span>💬 {item.comments}</span>
                      <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </motion.article>
              ))}
            </div>
          ))}
          {isLoading &&
            Array.from({ length: 3 }).map((_, index) => (
              <Skeleton key={`loader-${index}`} className="h-64 rounded-3xl" />
            ))}
        </div>
        <div ref={observerRef} className="h-16 w-full" aria-hidden />
        {error && (
          <div className="mt-4 rounded-2xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-xs text-rose-200">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
