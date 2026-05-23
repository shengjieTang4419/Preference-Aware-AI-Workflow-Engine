import logging
from datetime import datetime, timedelta
from typing import Optional, List

from crewai_web.web.database import get_pool
from crewai_web.web.domain.membership import (
    MembershipOut, TransactionOut, PricingPlan,
)

logger = logging.getLogger(__name__)

# ── 定价方案 ──────────────────────────────────────────

PRICING_PLANS = [
    PricingPlan(
        level="free", name="免费账户", price=0, period="永久",
        features=["基础文档生成", "基础数据分析", "每月 10 次创作"],
        scene_access="仅免费场景",
    ),
    PricingPlan(
        level="pro", name="Pro 会员", price=29.9, period="月",
        features=["全部文档类场景", "全部数据类场景", "无限次创作", "优先排队"],
        scene_access="免费 + 基础场景",
    ),
    PricingPlan(
        level="max", name="Max 会员", price=99.9, period="月",
        features=["全部场景（含音乐/视频）", "无限次创作", "最高优先级", "专属客服", "API 额度加倍"],
        scene_access="全部场景",
    ),
]

# 层级对应的可访问价格层级
TIER_ACCESS = {
    "free": ["free"],
    "pro": ["free", "basic"],
    "max": ["free", "basic", "premium"],
}


# ── 会员查询 ──────────────────────────────────────────

async def get_membership(user_id: int) -> MembershipOut:
    """获取用户会员信息"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT m.*, u.virtual_money
               FROM user_memberships m
               JOIN users u ON u.id = m.user_id
               WHERE m.user_id = $1""", user_id
        )
    if not row:
        return MembershipOut(user_id=user_id, level="free", virtual_money=0)

    data = dict(row)
    # 判断是否过期
    if data.get("expires_at") and data["expires_at"] < datetime.utcnow():
        data["is_expired"] = True
        data["level"] = "free"
    else:
        data["is_expired"] = False
    data["virtual_money"] = float(data.get("virtual_money") or 0)
    return MembershipOut(**data)


async def get_user_accessible_tiers(user_id: int) -> List[str]:
    """获取用户可访问的价格层级"""
    membership = await get_membership(user_id)
    level = "free" if membership.is_expired else membership.level
    return TIER_ACCESS.get(level, ["free"])


# ── 激活码 ──────────────────────────────────────────

async def activate_code(user_id: int, code: str) -> MembershipOut:
    """激活码升级"""
    # 解析激活码格式: PRO-3M-XXXXX / MAX-6M-XXXXX
    parts = code.upper().split("-")
    if len(parts) != 3 or parts[0] not in ("PRO", "MAX"):
        raise ValueError("无效的激活码格式")

    level = parts[0].lower()
    months = int(parts[1].replace("M", "")) if parts[1].endswith("M") else 1
    expires_at = datetime.utcnow() + timedelta(days=months * 30)

    pool = await get_pool()
    async with pool.acquire() as conn:
        # 获取当前等级
        current = await conn.fetchrow(
            "SELECT level FROM user_memberships WHERE user_id = $1", user_id
        )
        from_level = current["level"] if current else "free"

        # 更新会员
        await conn.execute(
            """INSERT INTO user_memberships (user_id, level, activation_code, activated_at, expires_at)
               VALUES ($1, $2, $3, NOW(), $4)
               ON CONFLICT (user_id) DO UPDATE
               SET level = $2, activation_code = $3, activated_at = NOW(), expires_at = $4""",
            user_id, level, code, expires_at,
        )

        # 记录流水
        await conn.execute(
            """INSERT INTO membership_transactions (user_id, action, from_level, to_level, activation_code, remark)
               VALUES ($1, 'activate', $2, $3, $4, $5)""",
            user_id, from_level, level, code, f"激活码升级: {from_level} → {level}, {months}个月",
        )

        # 自动安装该等级可访问的场景
        accessible = TIER_ACCESS.get(level, ["free"])
        await conn.execute(
            """INSERT INTO user_scenes (user_id, scene_id)
               SELECT $1, id FROM scene_configs
               WHERE price_tier = ANY($2) AND enabled = TRUE
               ON CONFLICT (user_id, scene_id) DO NOTHING""",
            user_id, accessible,
        )

    logger.info(f"用户 {user_id} 激活码成功: {from_level} → {level}")
    return await get_membership(user_id)


# ── 充值 ──────────────────────────────────────────

async def purchase_membership(user_id: int, level: str, months: int) -> MembershipOut:
    """充值会员"""
    if level not in ("pro", "max"):
        raise ValueError("无效的会员等级")

    # 检查是否降级
    pool = await get_pool()
    async with pool.acquire() as conn:
        current = await conn.fetchrow(
            "SELECT level, expires_at FROM user_memberships WHERE user_id = $1", user_id
        )
    current_level = current["level"] if current else "free"
    level_rank = {"free": 0, "pro": 1, "max": 2}
    if level_rank.get(current_level, 0) >= level_rank.get(level, 0):
        raise ValueError(f"当前已是 {current_level.upper()} 会员，无法购买同级或更低等级方案")

    plan = next((p for p in PRICING_PLANS if p.level == level), None)
    if not plan:
        raise ValueError("未找到对应套餐")

    total_amount = plan.price * months
    expires_at = datetime.utcnow() + timedelta(days=months * 30)

    async with pool.acquire() as conn:
        # 检查虚拟余额
        user = await conn.fetchrow("SELECT virtual_money FROM users WHERE id = $1", user_id)
        balance = float(user["virtual_money"] or 0)

        if balance < total_amount:
            raise ValueError(f"余额不足: 需要 ¥{total_amount:.2f}，当前余额 ¥{balance:.2f}")

        # 扣减余额
        await conn.execute(
            "UPDATE users SET virtual_money = virtual_money - $1 WHERE id = $2",
            total_amount, user_id,
        )

        from_level = current_level

        # 如果当前是同等级且未过期，续期
        if current and current["level"] == level and current.get("expires_at") and current["expires_at"] > datetime.utcnow():
            expires_at = current["expires_at"] + timedelta(days=months * 30)

        await conn.execute(
            """INSERT INTO user_memberships (user_id, level, activated_at, expires_at)
               VALUES ($1, $2, NOW(), $3)
               ON CONFLICT (user_id) DO UPDATE
               SET level = $2, activated_at = NOW(), expires_at = $3""",
            user_id, level, expires_at,
        )

        # 记录流水
        await conn.execute(
            """INSERT INTO membership_transactions (user_id, action, from_level, to_level, amount, remark)
               VALUES ($1, 'purchase', $2, $3, $4, $5)""",
            user_id, from_level, level, total_amount,
            f"充值 {months} 个月 {level.upper()} 会员, 扣款 ¥{total_amount:.2f}",
        )

        # 安装场景
        accessible = TIER_ACCESS.get(level, ["free"])
        await conn.execute(
            """INSERT INTO user_scenes (user_id, scene_id)
               SELECT $1, id FROM scene_configs
               WHERE price_tier = ANY($2) AND enabled = TRUE
               ON CONFLICT (user_id, scene_id) DO NOTHING""",
            user_id, accessible,
        )

    logger.info(f"用户 {user_id} 充值成功: {level} x{months}月, ¥{total_amount}")
    return await get_membership(user_id)


# ── 流水查询 ──────────────────────────────────────────

async def list_transactions(user_id: int, limit: int = 20) -> List[TransactionOut]:
    """获取用户充值流水"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM membership_transactions WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
            user_id, limit,
        )
    return [TransactionOut(**dict(r)) for r in rows]


# ── 用户已安装场景 ──────────────────────────────────────

async def get_user_installed_scenes(user_id: int) -> List[str]:
    """获取用户已安装的场景 ID 列表"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT scene_id FROM user_scenes WHERE user_id = $1", user_id
        )
    return [r["scene_id"] for r in rows]


async def install_scene(user_id: int, scene_id: str) -> bool:
    """用户安装场景"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 检查场景是否存在
        scene = await conn.fetchrow(
            "SELECT price_tier FROM scene_configs WHERE id = $1", scene_id
        )
        if not scene:
            raise ValueError(f"场景 '{scene_id}' 不存在")

        # 检查用户是否有权限（在同一连接内完成，避免竞态）
        membership = await get_membership(user_id)
        level = "free" if membership.is_expired else membership.level
        accessible = TIER_ACCESS.get(level, ["free"])
        if scene["price_tier"] not in accessible:
            raise ValueError(f"当前会员等级无权使用此场景，请升级会员")

        await conn.execute(
            """INSERT INTO user_scenes (user_id, scene_id)
               VALUES ($1, $2) ON CONFLICT (user_id, scene_id) DO NOTHING""",
            user_id, scene_id,
        )
    logger.info(f"用户 {user_id} 安装场景: {scene_id}")
    return True