import os
import time

class ChromaMemoryStore:
    """
    Mock implementation of a conversational memory store.
    Bypasses the Pydantic v1/v2 conflict natively present in the chromadb python client.
    """
    
    def __init__(self):
        # In a real app, this would connect to a DB. 
        # Here we just use an in-memory dictionary.
        print("[MemoryStore] Initialized Local Mock Memory Store (ChromaDB disabled due to Pydantic conflicts).")
        self.conversations = []

    def add_interaction(self, session_id: str, user_message: str, ai_response: str):
        """
        Stores a single back-and-forth interaction.
        """
        doc_text = f"USER: {user_message}\nJARVIS: {ai_response}"
        self.conversations.append({
            "session_id": session_id,
            "text": doc_text,
            "timestamp": time.time()
        })
        print(f"[MemoryStore] Saved interaction for session {session_id}")

    def search_context(self, query: str, n_results: int = 3) -> str:
        """
        Naive text search through the mocked memory.
        """
        if not self.conversations:
            return "No previous memory context found."
            
        # Very crude keyword match for the scaffold
        query_words = set(query.lower().split())
        
        scored_docs = []
        for doc in self.conversations:
            doc_words = set(doc["text"].lower().split())
            score = len(query_words.intersection(doc_words))
            if score > 0:
                scored_docs.append((score, doc))
                
        if not scored_docs:
            # If no direct keyword overlap, just return the most recent interaction
            most_recent = sorted(self.conversations, key=lambda x: x["timestamp"], reverse=True)[:n_results]
            context_blocks = "\n---\n".join([doc["text"] for doc in most_recent])
            return f"Retrieved Past Context (Most Recent):\n{context_blocks}"
            
        # Return the highest scored documents
        sorted_docs = sorted(scored_docs, key=lambda x: x[0], reverse=True)[:n_results]
        context_blocks = "\n---\n".join([doc[1]["text"] for doc in sorted_docs])
        return f"Retrieved Past Context (Keyword Match):\n{context_blocks}"
