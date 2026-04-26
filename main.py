import sys
import anthropic
from retriever import BM25Retriever

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

client = anthropic.Anthropic()
retriever = BM25Retriever()

print(f"Loaded {len(retriever.corpus)} chunks")

conversation_history = []


def expand_query(query):
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=60,
        system="You are a Code V optical design software expert. "
               "Extract 4-8 English technical keywords from the user query "
               "that would appear in the Code V manual. "
               "Output keywords only, space-separated. No explanations.",
        messages=[{"role": "user", "content": query}]
    )
    return resp.content[0].text.strip()


def ask_codev(query, chunks, history):
    context = "\n\n".join(
        f"[Source: {c['folder']}/{c['filename']} | {c['title']}]\n{c['text']}"
        for c in chunks
    )

    system_prompt = """You are a strict Code V assistant.
Answer ONLY based on the provided manual excerpts.
Always follow the output format exactly.
Do NOT add content before [From Manual].
Do NOT use knowledge outside the provided excerpts."""

    user_message = f"""User question:
{query}

Manual excerpts:
{context}

---

OUTPUT FORMAT (MANDATORY):

[From Manual]
- Relevant command(s): ...
- Description: ...
- Syntax: ...
- Example: ...

[Additional Explanation]
- When to use:
- Practical interpretation:
- Tips:
- Common mistakes:

If the manual excerpts do not contain enough information, say so clearly."""

    messages = history + [{"role": "user", "content": user_message}]

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=system_prompt,
        messages=messages,
    )
    return resp.content[0].text.strip()


# ==============================
# Main loop
# ==============================
print("\nCode V Assistant (type 'exit' to quit)\n")

while True:
    query = input("Ask CodeV: ").strip()
    if not query:
        continue
    if query.lower() in ("exit", "quit", "q"):
        print("Goodbye.")
        break

    # 1. 쿼리 확장
    expanded = expand_query(query)
    print(f"[Search terms: {expanded}]")

    # 2. BM25 검색
    chunks = retriever.search(expanded, top_k=5)
    if not chunks:
        print("No relevant manual pages found.\n")
        continue

    print(f"[Found {len(chunks)} relevant sections]\n")

    # 3. Claude 답변 생성
    answer = ask_codev(query, chunks, conversation_history)

    # 4. [From Manual] 이전 내용 제거
    start = answer.find("[From Manual]")
    if start != -1:
        answer = answer[start:]

    print("\n=== Answer ===\n")
    print(answer)
    print()

    # 5. 대화 기록 유지 (최근 3턴)
    conversation_history.append({"role": "user", "content": query})
    conversation_history.append({"role": "assistant", "content": answer})
    if len(conversation_history) > 6:
        conversation_history = conversation_history[-6:]
