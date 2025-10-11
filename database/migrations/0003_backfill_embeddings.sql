INSERT INTO public.tool_embedding (tool_id, embedding, model, updated_at)
SELECT t.id,
       public.hashed_embed(t.name || ' ' || coalesce(t.description,'') || ' ' || array_to_string(coalesce(t.tags, ARRAY[]::text[]),' ')),
       'hashed-768-sql',
       now()
FROM public.tool t
ON CONFLICT (tool_id) DO UPDATE
SET embedding = EXCLUDED.embedding,
    model     = EXCLUDED.model,
    updated_at= now();
