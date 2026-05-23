-- 创意工坊数据库初始化脚本
-- 由 Docker entrypoint 自动执行

-- 启用 pgvector 扩展（向量检索预留）
CREATE EXTENSION IF NOT EXISTS vector;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    virtual_money DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 场景配置表（模版市场 + 创意工坊）
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创作记录表
CREATE TABLE IF NOT EXISTS creations (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    scene_id VARCHAR(50) REFERENCES scene_configs(id),
    input_text TEXT,
    input_files TEXT[],
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    output_dir TEXT,
    output_files TEXT[],
    error_message TEXT,
    execution_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创作制品表
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
);

-- 用户会员表
CREATE TABLE IF NOT EXISTS user_memberships (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(id),
    level VARCHAR(20) NOT NULL DEFAULT 'free',
    activation_code VARCHAR(100),
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会员充值流水表
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
);

-- 用户已安装场景表
CREATE TABLE IF NOT EXISTS user_scenes (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    scene_id VARCHAR(50) REFERENCES scene_configs(id),
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, scene_id)
);

-- 插入默认场景配置
INSERT INTO scene_configs (id, icon, title, subtitle, placeholder, category, tags, output_format, sort_order, price_tier, exec_mode)
VALUES
    ('document', '📝', '结构化文档', '输入想法，AI 生成专业文档',
     '例如：帮我写一份竞品分析报告，分析 xxx 行业的前 3 名...',
     'document', '{热门}', 'markdown', 1, 'free', 'auto'),
    ('data-analysis', '📊', '数据分析', '上传数据，AI 生成分析报告',
     '例如：帮我分析这个 CSV 的用户留存趋势...',
     'data', '{热门}', 'markdown', 2, 'free', 'auto'),
    ('ppt', '🎨', '产品 PPT', '描述产品，AI 生成演示文稿',
     '例如：帮我做一个 SaaS 产品的融资 PPT...',
     'document', '{推荐}', 'pptx', 3, 'basic', 'manual'),
    ('code', '💻', '写代码', '描述需求，AI 生成代码项目',
     '例如：帮我写一个 Todo App，用 React + TypeScript...',
     'code', '{}', 'zip', 4, 'free', 'auto'),
    ('excel', '📈', 'Excel 图表', '上传数据，AI 生成可视化图表',
     '例如：帮我做一个销售数据看板...',
     'data', '{}', 'xlsx', 5, 'basic', 'auto'),
    ('music', '🎵', '生成音乐', '描述风格，AI 创作音乐',
     '例如：生成一段 30 秒的轻快电子音乐...',
     'media', '{新上线}', 'mp3', 6, 'premium', 'manual'),
    ('video', '🎬', '制作视频', '输入脚本，AI 生成视频',
     '例如：帮我做一个产品宣传短视频...',
     'media', '{即将上线}', 'mp4', 7, 'premium', 'manual'),
    ('game', '🎮', '做小游戏', '描述玩法，AI 生成可玩的游戏',
     '例如：帮我做一个贪吃蛇小游戏...',
     'code', '{即将上线}', 'html', 8, 'basic', 'auto')
ON CONFLICT (id) DO NOTHING;
