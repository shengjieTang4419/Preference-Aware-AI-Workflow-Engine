"""数据库连接模块 - PostgreSQL"""
import logging
from typing import Optional

import asyncpg

from crewai_web.web.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """获取数据库连接池"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            min_size=1,
            max_size=10,
        )
    return _pool


async def close_pool():
    """关闭连接池"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("数据库连接池已关闭")


async def init_db():
    """初始化数据库表"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scenes (
                id VARCHAR(50) PRIMARY KEY,
                icon VARCHAR(10) NOT NULL,
                title VARCHAR(100) NOT NULL,
                subtitle VARCHAR(200) NOT NULL,
                placeholder TEXT,
                category VARCHAR(20) NOT NULL DEFAULT 'document',
                tags TEXT[] DEFAULT '{}',
                output_format VARCHAR(20) NOT NULL DEFAULT 'markdown',
                enabled BOOLEAN DEFAULT TRUE,
                sort_order INT DEFAULT 0,
                crew_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS creations (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id),
                scene_id VARCHAR(50) REFERENCES scenes(id),
                input_text TEXT,
                input_files TEXT[],
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                output_dir TEXT,
                output_files TEXT[],
                error_message TEXT,
                execution_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)


        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scene_configs (
                id VARCHAR(50) PRIMARY KEY,
                icon VARCHAR(10) NOT NULL,
                title VARCHAR(100) NOT NULL,
                subtitle VARCHAR(200) NOT NULL,
                placeholder TEXT,
                category VARCHAR(20) NOT NULL DEFAULT 'document',
                tags TEXT[] DEFAULT '{}',
                output_format VARCHAR(20) NOT NULL DEFAULT 'markdown',
                enabled BOOLEAN DEFAULT TRUE,
                visible BOOLEAN DEFAULT TRUE,
                sort_order INT DEFAULT 0,
                price_tier VARCHAR(20) DEFAULT 'free',
                exec_mode VARCHAR(20) DEFAULT 'manual',
                output_dir TEXT,
                crew_template TEXT,
                description TEXT,
                artifact_skills JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memberships (
                id SERIAL PRIMARY KEY,
                user_id INT UNIQUE REFERENCES users(id),
                level VARCHAR(20) NOT NULL DEFAULT 'free',
                activation_code VARCHAR(100),
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS membership_transactions (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id),
                action VARCHAR(20) NOT NULL,
                from_level VARCHAR(20),
                to_level VARCHAR(20),
                amount DECIMAL(10,2) DEFAULT 0,
                activation_code VARCHAR(100),
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_scenes (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id),
                scene_id VARCHAR(50) REFERENCES scene_configs(id),
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, scene_id)
            )
        """)

        # 给 users 表追加 virtual_money 字段（如果不存在）
        await conn.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS virtual_money DECIMAL(12,2) DEFAULT 0
        """)

        # 创建默认会员记录（已有用户）
        await conn.execute("""
            INSERT INTO user_memberships (user_id, level)
            SELECT id, 'free' FROM users
            WHERE id NOT IN (SELECT user_id FROM user_memberships)
            ON CONFLICT (user_id) DO NOTHING
        """)

        # 插入默认场景卡片（如果为空）
        count = await conn.fetchval("SELECT COUNT(*) FROM scene_configs")
        if count == 0:
                await conn.executemany(
                """INSERT INTO scene_configs (id, icon, title, subtitle, placeholder, category, tags, output_format, sort_order, price_tier, exec_mode, artifact_skills)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)""",
                [
                    ('document', '📝', '结构化文档', '输入想法，AI 生成专业文档',
                     '例如：帮我写一份竞品分析报告，分析 xxx 行业的前 3 名...',
                     'document', ['热门'], 'markdown', 1, 'free', 'auto', '["documentation-writer"]'),
                    ('data-analysis', '📊', '数据分析', '上传数据，AI 生成分析报告',
                     '例如：帮我分析这个 CSV 的用户留存趋势...',
                     'data', ['热门'], 'markdown', 2, 'free', 'auto', '["excel-automation"]'),
                    ('ppt', '🎨', '产品 PPT', '描述产品，AI 生成演示文稿',
                     '例如：帮我做一个 SaaS 产品的融资 PPT...',
                     'document', ['推荐'], 'pptx', 3, 'basic', 'manual', '["pptx"]'),
                    ('code', '💻', '写代码', '描述需求，AI 生成代码项目',
                     '例如：帮我写一个 Todo App，用 React + TypeScript...',
                     'code', [], 'zip', 4, 'free', 'auto', '["code-generator"]'),
                    ('excel', '📈', 'Excel 图表', '上传数据，AI 生成可视化图表',
                     '例如：帮我做一个销售数据看板...',
                     'data', [], 'xlsx', 5, 'basic', 'auto', '["excel-automation"]'),
                    ('music', '🎵', '生成音乐', '描述风格，AI 创作音乐',
                     '例如：生成一段 30 秒的轻快电子音乐...',
                     'media', ['新上线'], 'mp3', 6, 'premium', 'manual'),
                    ('video', '🎬', '制作视频', '输入脚本，AI 生成视频',
                     '例如：帮我做一个产品宣传短视频...',
                     'media', ['即将上线'], 'mp4', 7, 'premium', 'manual'),
                    ('game', '🎮', '做小游戏', '描述玩法，AI 生成可玩的游戏',
                     '例如：帮我做一个贪吃蛇小游戏...',
                     'code', ['即将上线'], 'html', 8, 'basic', 'auto'),
                ]
            )


        await conn.execute("""
            CREATE TABLE IF NOT EXISTS creative_artifacts (
                id SERIAL PRIMARY KEY,
                execution_id VARCHAR(100) UNIQUE NOT NULL,
                user_id INT REFERENCES users(id),
                scene_id VARCHAR(50) NOT NULL,
                title VARCHAR(200),
                description TEXT,
                output_type VARCHAR(20),
                output_dir TEXT,
                output_files TEXT[],
                preview_text TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # 给 scene_configs 追加 artifact_skills 字段（兼容已有数据库）
        await conn.execute("""
            ALTER TABLE scene_configs ADD COLUMN IF NOT EXISTS artifact_skills JSONB DEFAULT '[]'
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS artifact_skill_executions (
                id SERIAL PRIMARY KEY,
                execution_id VARCHAR(100) NOT NULL,
                skill_name VARCHAR(100) NOT NULL,
                step_index INT NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                input_summary TEXT,
                output_files TEXT[],
                output_metadata JSONB DEFAULT '{}',
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 给 creative_artifacts 追加 skill_chain 和 crew_execution_id（兼容已有数据库）
        await conn.execute("""
            ALTER TABLE creative_artifacts ADD COLUMN IF NOT EXISTS skill_chain JSONB DEFAULT '[]'
        """)
        await conn.execute("""
            ALTER TABLE creative_artifacts ADD COLUMN IF NOT EXISTS crew_execution_id VARCHAR(100)
        """)

        # 给所有免费用户自动安装免费场景
        await conn.execute("""
            INSERT INTO user_scenes (user_id, scene_id)
            SELECT u.id, sc.id
            FROM users u
            CROSS JOIN scene_configs sc
            WHERE sc.price_tier = 'free' AND sc.enabled = TRUE
            ON CONFLICT (user_id, scene_id) DO NOTHING
        """)

    logger.info("数据库表初始化完成")