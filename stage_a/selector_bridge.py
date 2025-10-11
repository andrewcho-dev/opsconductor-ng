import os, asyncpg
from typing import List, Dict, Any
from selector import candidate_tools_from_intent

async def select_candidates_for_prompt(user_intent: str, k: int = 10) -> List[Dict[str, Any]]:
    conn = await asyncpg.connect(dsn=os.environ["DATABASE_URL"])
    try:
        stubs = await candidate_tools_from_intent(conn, user_intent, k=k)
        # keep the payload compact for token budget
        return [
            {
                "key": getattr(s, "tool_name", getattr(s, "name", "")),
                "name": getattr(s, "tool_name", getattr(s, "name", "")),
                "short_desc": (getattr(s, "description", "") or "")[:160],
            }
            for s in stubs
        ]
    finally:
        await conn.close()
