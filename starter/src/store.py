"""Store and search vectors using PostgreSQL + pgvector."""
import json
from typing import Any
import psycopg
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        """Retain connection settings; validate model dimensions."""
        if not database_url:
            raise ValueError("database_url cannot be empty")
        self.database_url = database_url
        self.dimensions = int(dimensions)

    def create_schema(self) -> None:
        """Create table with vector column and metadata indexes."""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        id TEXT PRIMARY KEY,
                        strategy TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INT NOT NULL,
                        chapter TEXT,
                        section TEXT,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self.dimensions}),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_strategy
                    ON document_chunks (strategy);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_chapter
                    ON document_chunks (chapter);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_page
                    ON document_chunks (page);
                """)
            conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Validate lengths and write stable records, removing previous chunks of strategy."""
        if len(chunks) != len(vectors):
            raise ValueError(f"Mismatch between chunks count ({len(chunks)}) and vectors count ({len(vectors)})")
        if not chunks:
            return

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                # Remove obsolete chunks for this strategy to prevent duplication upon re-run
                cur.execute("DELETE FROM document_chunks WHERE strategy = %s;", (strategy,))

                insert_sql = """
                    INSERT INTO document_chunks (
                        id, strategy, chunk_id, document_id, source, page,
                        chapter, section, text, metadata, embedding
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding,
                        created_at = CURRENT_TIMESTAMP;
                """

                rows = []
                for chunk, vector in zip(chunks, vectors):
                    record_id = f"{strategy}_{chunk.chunk_id}"
                    chapter = chunk.metadata.get("chapter", "")
                    section = chunk.metadata.get("section", "")
                    meta_json = json.dumps(chunk.metadata, ensure_ascii=False)
                    # Convert vector float list to string format: '[0.1, 0.2, ...]'
                    vec_str = f"[{', '.join(str(v) for v in vector)}]"
                    rows.append((
                        record_id, strategy, chunk.chunk_id, chunk.document_id,
                        chunk.source, chunk.page, chapter, section, chunk.text,
                        meta_json, vec_str
                    ))

                cur.executemany(insert_sql, rows)
            conn.commit()

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Filter metadata, rank by cosine distance (<=>), and return top-k."""
        if len(query_vector) != self.dimensions:
            raise ValueError(f"Query vector dim ({len(query_vector)}) does not match index dim ({self.dimensions})")

        vec_str = f"[{', '.join(str(v) for v in query_vector)}]"
        where_clauses = ["strategy = %(strategy)s"]
        params: dict[str, Any] = {
            "strategy": strategy,
            "qvec": vec_str,
            "top_k": top_k
        }

        if filters:
            for k, v in filters.items():
                if k == "chapter" and isinstance(v, str):
                    # Match chapter prefix or substring e.g. "Chapter 1"
                    where_clauses.append("chapter ILIKE %(filt_chapter)s")
                    params["filt_chapter"] = f"%{v}%"
                elif k == "section" and isinstance(v, str):
                    where_clauses.append("section ILIKE %(filt_section)s")
                    params["filt_section"] = f"%{v}%"
                elif k == "page":
                    where_clauses.append("page = %(filt_page)s")
                    params["filt_page"] = int(v)
                else:
                    where_clauses.append(f"metadata->>%(k_{k})s = %(v_{k})s")
                    params[f"k_{k}"] = str(k)
                    params[f"v_{k}"] = str(v)

        where_sql = " AND ".join(where_clauses)
        query_sql = f"""
            SELECT
                chunk_id,
                document_id,
                source,
                page,
                chapter,
                section,
                text,
                metadata,
                1 - (embedding <=> %(qvec)s::vector) AS similarity_score
            FROM document_chunks
            WHERE {where_sql}
            ORDER BY embedding <=> %(qvec)s::vector ASC
            LIMIT %(top_k)s;
        """

        hits: list[dict[str, Any]] = []
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query_sql, params)
                for row in cur.fetchall():
                    hits.append({
                        "chunk_id": row[0],
                        "document_id": row[1],
                        "source": row[2],
                        "page": row[3],
                        "chapter": row[4],
                        "section": row[5],
                        "text": row[6],
                        "metadata": row[7] if isinstance(row[7], dict) else json.loads(row[7]),
                        "score": float(row[8])
                    })

        return hits
