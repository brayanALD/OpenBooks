// Espejo de backend/app/api/v1/library.py (LibraryOut).

import type { BookSummary } from "@/types/catalog";

export type LibraryUnavailableBook = { book_id: string; title: string; author_name: string; cover: string };

export type Library = { items: BookSummary[]; unavailable: LibraryUnavailableBook[] };
