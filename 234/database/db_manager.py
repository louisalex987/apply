import aiosqlite
import json
from typing import Optional, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "naruto_game.db"):
        self.db_path = db_path
    
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Table des joueurs
            await db.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    village TEXT,
                    clan TEXT,
                    level INTEGER DEFAULT 1,
                    exp INTEGER DEFAULT 0,
                    chakra INTEGER DEFAULT 100,
                    health INTEGER DEFAULT 100,
                    stamina INTEGER DEFAULT 100,
                    stats TEXT,
                    jutsu_list TEXT,
                    ryo INTEGER DEFAULT 500,
                    last_daily TIMESTAMP
                )
            ''')
            
            # Table des combats
            await db.execute('''
                CREATE TABLE IF NOT EXISTS battles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_id INTEGER,
                    player2_id INTEGER,
                    status TEXT,
                    turn INTEGER DEFAULT 1,
                    battle_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    async def create_player(self, user_id: int, name: str, village: str, clan: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            stats = json.dumps({
                "ninjutsu": 10,
                "genjutsu": 10,
                "taijutsu": 10,
                "speed": 10,
                "strength": 10,
                "intelligence": 10
            })
            
            jutsu_list = json.dumps(["Clone no Jutsu", "Kawarimi no Jutsu"])
            
            await db.execute('''
                INSERT INTO players 
                (user_id, name, village, clan, stats, jutsu_list)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name, village, clan, stats, jutsu_list))
            
            await db.commit()
    
    async def get_player(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM players WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
    
    async def update_player(self, user_id: int, **kwargs):
        async with aiosqlite.connect(self.db_path) as db:
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            
            await db.execute(
                f'UPDATE players SET {set_clause} WHERE user_id = ?',
                values
            )
            await db.commit()