import os
import time
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorMemoryStore:
    def __init__(self, storage_dir="backend/memory_storage"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        
        self.index_path = os.path.join(self.storage_dir, "episodic.index")
        self.meta_path = os.path.join(self.storage_dir, "episodic_meta.json")
        
        # 384 dimensions for all-MiniLM-L6-v2
        self.dimension = 384
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"[VectorStore] Creating encoder failed: {e}")
            self.encoder = None
        
        self.metadata = []
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r") as f:
                self.metadata = json.load(f)
            print(f"[VectorStore] Loaded existing FAISS index with {self.index.ntotal} memories.")
            self.prune_old_memories(max_age_days=30)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            print("[VectorStore] Created new FAISS episodic memory index.")

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f)

    def prune_old_memories(self, max_age_days=30):
        if not self.metadata or not self.encoder: return
        current_time = time.time()
        max_age_seconds = max_age_days * 86400
        
        valid_indices = []
        for i, meta in enumerate(self.metadata):
            if current_time - meta["timestamp"] < max_age_seconds:
                valid_indices.append(i)
                
        if len(valid_indices) == len(self.metadata):
            return
            
        print(f"[VectorStore] Pruning {len(self.metadata) - len(valid_indices)} decayed memories.")
        
        # Rebuild index and metadata
        new_metadata = [self.metadata[i] for i in valid_indices]
        
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        for meta in new_metadata:
            embedding = self.encoder.encode([meta["text"]])
            faiss.normalize_L2(embedding)
            self.index.add(embedding)
            self.metadata.append(meta)
            
        self._save()

    def add_interaction(self, session_id: str, user_message: str, ai_response: str):
        if not self.encoder: return
        doc_text = f"USER: {user_message}\nJARVIS: {ai_response}"
        
        # Create embedding
        embedding = self.encoder.encode([doc_text])
        faiss.normalize_L2(embedding) # Normalize for cosine similarity equivalent
        
        self.index.add(embedding)
        
        self.metadata.append({
            "session_id": session_id,
            "text": doc_text,
            "timestamp": time.time()
        })
        self._save()
        print(f"[VectorStore] Saved interaction to Episodic FAISS index.")

    def search_context(self, query: str, n_results: int = 3) -> str:
        if not self.encoder or self.index.ntotal == 0:
            return "No previous episodic memory found."
            
        embedding = self.encoder.encode([query])
        faiss.normalize_L2(embedding)
        
        # Search for slightly more than n_results to allow decay reranking
        search_k = min(n_results * 2, self.index.ntotal)
        distances, indices = self.index.search(embedding, search_k)
        
        results = []
        current_time = time.time()
        
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1: continue
            
            meta = self.metadata[idx]
            # Time penalty: increase distance (lower similarity) slightly for older memories
            # E.g., add 0.05 to distance for every hour (3600s) old
            age_seconds = current_time - meta["timestamp"]
            time_penalty = (age_seconds / 3600.0) * 0.05
            adjusted_dist = dist + time_penalty
            
            results.append((adjusted_dist, meta["text"]))
            
        # Re-sort based on decayed distance (lower is better in L2)
        results.sort(key=lambda x: x[0])
        
        final_results = results[:n_results]
        
        context_blocks = "\n---\n".join([r[1] for r in final_results])
        return f"Retrieved Episodic Memory:\n{context_blocks}"
