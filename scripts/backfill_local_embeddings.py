import os, sys, psycopg2
from sentence_transformers import SentenceTransformer

db = os.environ["DATABASE_URL"]
conn = psycopg2.connect(db); cur = conn.cursor()

cur.execute("SELECT id, name, COALESCE(description,''), COALESCE(tags, ARRAY[]::text[]) FROM public.tool ORDER BY id")
rows = cur.fetchall()
print("tool rows:", len(rows))
if not rows:
    print("No tools found; aborting backfill."); sys.exit(0)

model_name = "nomic-ai/nomic-embed-text-v1.5"   # 768-dim local model
print("loading model:", model_name, flush=True)
model = SentenceTransformer(model_name)

def vec(v): return "[" + ",".join(f"{float(x):.6f}" for x in v) + "]"

B = 12  # conservative batch for slim container
for i in range(0, len(rows), B):
    chunk = rows[i:i+B]
    texts = [f"{r[1]}\n{r[2]}\n{' '.join(r[3])}" for r in chunk]
    embs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    for (tool_id, *_), e in zip(chunk, embs):
        cur.execute("""
          INSERT INTO public.tool_embedding (tool_id, embedding, model, updated_at)
          VALUES (%s, %s::vector, %s, NOW())
          ON CONFLICT (tool_id) DO UPDATE
          SET embedding = EXCLUDED.embedding, model = EXCLUDED.model, updated_at = NOW();
        """, (tool_id, vec(e.tolist()), model_name))
    conn.commit()
    print(f"Upserted {min(i+B, len(rows))}/{len(rows)}", flush=True)

cur.close(); conn.close()
print("Backfill complete.", flush=True)
