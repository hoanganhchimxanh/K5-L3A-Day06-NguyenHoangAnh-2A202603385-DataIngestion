"""Choose a real embedding provider (API or local) and implement this contract."""
import json
import os
import time
import urllib.error
import urllib.request
from typing import Protocol


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Production embedder supporting OpenAI, OpenRouter, and Gemini APIs.
    
    Uses standard library urllib.request to avoid external dependency issues.
    Never falls back to mock or random vectors.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        env_model = os.getenv("EMBEDDING_MODEL", "").strip()
        
        if self.openai_key and not self.openai_key.startswith("your_"):
            self.provider = "openai"
            # If user provided a chat model name like gpt-5.4-mini in .env, default to official embedding model
            if model_name:
                self.model_name = model_name
            elif env_model and "embedding" in env_model:
                self.model_name = env_model
            else:
                self.model_name = "text-embedding-3-small"
            self.dimensions = 1536
            self.endpoint = "https://api.openai.com/v1/embeddings"
            self.auth_header = {"Authorization": f"Bearer {self.openai_key}"}
        elif self.openrouter_key and not self.openrouter_key.startswith("your_"):
            self.provider = "openrouter"
            self.model_name = model_name or (env_model if env_model and "embedding" in env_model else "openai/text-embedding-3-small")
            self.dimensions = 1536
            self.endpoint = "https://openrouter.ai/api/v1/embeddings"
            self.auth_header = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "HTTP-Referer": "https://localhost",
                "X-Title": "Data-Ingestion-Lab"
            }
        elif self.gemini_key and not self.gemini_key.startswith("your_"):
            self.provider = "gemini"
            self.model_name = model_name or "text-embedding-004"
            self.dimensions = 768
            self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:batchEmbedContents?key={self.gemini_key}"
            self.auth_header = {}
        else:
            raise ValueError(
                "No valid API key found for OpenAI, OpenRouter, or Gemini in .env. "
                "Real embeddings are required by GUIDE.md (mock vectors are prohibited)."
            )

    def _request_openai_compatible(self, texts: list[str]) -> list[list[float]]:
        """Call OpenAI/OpenRouter embeddings endpoint."""
        payload = json.dumps({
            "model": self.model_name,
            "input": texts
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            **self.auth_header
        }

        req = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                # Sort by index to ensure original order
                sorted_items = sorted(res_data["data"], key=lambda x: x["index"])
                vectors = [item["embedding"] for item in sorted_items]
                if vectors and len(vectors[0]) != self.dimensions:
                    self.dimensions = len(vectors[0])
                return vectors
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Embedding API error ({self.provider}) HTTP {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Embedding request failed ({self.provider}): {e}") from e

    def _request_gemini(self, texts: list[str]) -> list[list[float]]:
        """Call Gemini batchEmbedContents endpoint."""
        requests = [
            {"model": f"models/{self.model_name}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        payload = json.dumps({"requests": requests}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                vectors = [item["values"] for item in res_data.get("embeddings", [])]
                if vectors and len(vectors[0]) != self.dimensions:
                    self.dimensions = len(vectors[0])
                return vectors
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini Embedding error HTTP {e.code}: {err_body}") from e

    def embed_documents(self, texts: list[str], batch_size: int = 40) -> list[list[float]]:
        """Return one vector per input text in batches."""
        if not texts:
            return []

        all_vectors: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            if self.provider in ("openai", "openrouter"):
                vectors = self._request_openai_compatible(batch)
            elif self.provider == "gemini":
                vectors = self._request_gemini(batch)
            else:
                raise RuntimeError(f"Unsupported provider: {self.provider}")

            all_vectors.extend(vectors)
            # Brief pause to respect API rate limits
            if i + batch_size < len(texts):
                time.sleep(0.1)

        return all_vectors

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        result = self.embed_documents([question])
        if not result:
            raise RuntimeError("Embed query returned no vector")
        return result[0]
