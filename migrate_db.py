import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DB_PATH = Path("./data/imgbed.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


async def migrate():
    if not DB_PATH.exists():
        print("数据库不存在，首次启动时会自动创建")
        return

    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        print("开始迁移数据库...")
        
        try:
            await conn.execute(text("ALTER TABLE media_files ADD COLUMN updated_at DATETIME"))
            print("已添加 updated_at 列")
        except Exception as e:
            print(f"updated_at 列可能已存在: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE media_files ADD COLUMN expires_at DATETIME"))
            print("已添加 expires_at 列")
        except Exception as e:
            print(f"expires_at 列可能已存在: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE media_files ADD COLUMN is_expired BOOLEAN DEFAULT 0"))
            print("已添加 is_expired 列")
        except Exception as e:
            print(f"is_expired 列可能已存在: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE media_files ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
            print("已添加 is_deleted 列")
        except Exception as e:
            print(f"is_deleted 列可能已存在: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE media_files ADD COLUMN deleted_at DATETIME"))
            print("已添加 deleted_at 列")
        except Exception as e:
            print(f"deleted_at 列可能已存在: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE media_files ADD COLUMN deleted_reason TEXT"))
            print("已添加 deleted_reason 列")
        except Exception as e:
            print(f"deleted_reason 列可能已存在: {e}")
        
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_media_files_expires_at ON media_files(expires_at)"))
            print("已创建 expires_at 索引")
        except Exception as e:
            print(f"索引创建可能已存在: {e}")
        
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_media_files_is_expired ON media_files(is_expired)"))
            print("已创建 is_expired 索引")
        except Exception as e:
            print(f"索引创建可能已存在: {e}")
        
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_media_files_is_deleted ON media_files(is_deleted)"))
            print("已创建 is_deleted 索引")
        except Exception as e:
            print(f"索引创建可能已存在: {e}")

    await engine.dispose()
    print("数据库迁移完成!")


if __name__ == "__main__":
    asyncio.run(migrate())
