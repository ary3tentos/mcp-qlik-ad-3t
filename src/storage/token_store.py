import aiosqlite
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class TokenStore:
    def __init__(self):
        db_path = os.getenv("TOKEN_DB_PATH", "tokens.db")
        self.db_path = db_path
    
    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS qlik_tokens (
                    user_id TEXT PRIMARY KEY,
                    refresh_token TEXT NOT NULL,
                    access_token TEXT,
                    expires_at REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            await db.commit()
    
    async def close(self):
        pass
    
    async def save_tokens(self, user_id: str, refresh_token: str, access_token: Optional[str] = None, expires_in: Optional[int] = None):
        now = datetime.utcnow().timestamp()
        expires_at = None
        if expires_in:
            expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).timestamp()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO qlik_tokens 
                (user_id, refresh_token, access_token, expires_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, refresh_token, access_token, expires_at, now, now))
            await db.commit()
    
    async def get_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT refresh_token, access_token, expires_at 
                FROM qlik_tokens 
                WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "refresh_token": row["refresh_token"],
                        "access_token": row["access_token"],
                        "expires_at": row["expires_at"]
                    }
                return None
    
    async def update_access_token(self, user_id: str, access_token: str, expires_in: int):
        now = datetime.utcnow().timestamp()
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).timestamp()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE qlik_tokens 
                SET access_token = ?, expires_at = ?, updated_at = ?
                WHERE user_id = ?
            """, (access_token, expires_at, now, user_id))
            await db.commit()
    
    async def delete_tokens(self, user_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM qlik_tokens WHERE user_id = ?", (user_id,))
            await db.commit()
    
    async def is_token_expired(self, user_id: str) -> bool:
        tokens = await self.get_tokens(user_id)
        if not tokens or not tokens.get("expires_at"):
            return True
        return datetime.utcnow().timestamp() >= tokens["expires_at"]
