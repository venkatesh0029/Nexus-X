import os
import json
import networkx as nx

class SemanticMemoryGraph:
    def __init__(self, storage_dir="backend/memory_storage"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.graph_path = os.path.join(self.storage_dir, "semantic_graph.json")
        self.graph = nx.DiGraph()
        self._load()

    def _load(self):
        if os.path.exists(self.graph_path):
            try:
                with open(self.graph_path, "r") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
                print(f"[SemanticGraph] Loaded explicit facts graph. {self.graph.number_of_nodes()} nodes.")
            except Exception as e:
                print(f"[SemanticGraph] Error loading graph: {e}")

    def _save(self):
        data = nx.node_link_data(self.graph)
        with open(self.graph_path, "w") as f:
            json.dump(data, f, indent=2)

    def extract_and_add_fact(self, text: str):
        """
        Parses explicit fact syntax added by the UI or planner.
        Format expected: FACT: Subject -> predicate -> Object
        """
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("FACT:"):
                try:
                    parts = line.replace("FACT:", "").split("->")
                    if len(parts) == 3:
                        subj, pred, obj = [p.strip() for p in parts]
                        self.graph.add_edge(subj, obj, relation=pred)
                        print(f"[SemanticGraph] Added explicit fact: {subj} -[{pred}]-> {obj}")
                except Exception:
                    pass
        self._save()

    def query_facts(self, query: str) -> str:
        """
        Naively extracts explicit facts matching query terms.
        """
        if self.graph.number_of_edges() == 0:
            return ""
            
        topics = [t.lower() for t in query.split() if len(t) > 3]
        facts = []
        for u, v, data in self.graph.edges(data=True):
            relation = data.get("relation", "related to")
            # If any significant query word matches the subject or object
            if not topics or any(t in u.lower() or t in v.lower() or t in relation.lower() for t in topics):
                facts.append(f"{u} {relation} {v}")
        
        if facts:
            return "Verified Explicit Facts:\n- " + "\n- ".join(facts)
        return ""
