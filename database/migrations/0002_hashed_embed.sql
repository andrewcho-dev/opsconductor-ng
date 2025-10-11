CREATE OR REPLACE FUNCTION public.hashed_embed(txt text)
RETURNS vector
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$
WITH toks AS (
  SELECT lower(unnest(regexp_split_to_array(coalesce(txt,''), E'[^a-z0-9]+'))) AS tok
),
dims AS (
  SELECT (abs(hashtext(tok)) % 768) AS dim, count(*)::float4 AS val
  FROM toks WHERE tok <> '' GROUP BY 1
),
series AS (
  SELECT gs.i, coalesce(d.val,0)::float4 AS val
  FROM generate_series(0,767) AS gs(i)
  LEFT JOIN dims d ON d.dim = gs.i
)
SELECT (
  '[' || string_agg(to_char(series.val,'FM999999990.999999'), ',' ORDER BY series.i) || ']'
)::vector
FROM series;
$$;
