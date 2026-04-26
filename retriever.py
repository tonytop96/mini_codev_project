import json
import re
from rank_bm25 import BM25Okapi

CORPUS_PATH = r"d:\05_Claude Project\mini_codev_project\corpus.json"


def tokenize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


class BM25Retriever:
    def __init__(self, corpus_path=CORPUS_PATH):
        with open(corpus_path, encoding="utf-8") as f:
            self.corpus = json.load(f)
        tokenized = [tokenize(c["title"] + " " + c["text"]) for c in self.corpus]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query, top_k=5):
        tokens = tokenize(query)
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.corpus[i] for i in top_indices if scores[i] > 0]


if __name__ == "__main__":
    print("Loading corpus and building BM25 index...")
    r = BM25Retriever()
    print(f"Indexed {len(r.corpus)} chunks\n")

    tests = [
        "thickness variable control",
        "draw circle",
        "optimize lens",
        "EVA command",
    ]
    for q in tests:
        results = r.search(q, top_k=3)
        print(f"Query: {q!r}")
        for c in results:
            print(f"  [{c['folder']}] {c['title'][:60]}")
        print()
