<template>
  <div class="membership-page">
    <!-- 会员信息卡片 -->
    <div class="member-card" :class="membership.level">
      <div class="member-card-left">
        <div class="level-icon">{{ levelIcon }}</div>
        <div class="member-info">
          <h2>{{ levelName }}</h2>
          <p class="expire-text">
            <template v-if="membership.level === 'free'">永久有效</template>
            <template v-else-if="membership.is_expired">已过期，请续费</template>
            <template v-else>有效期至 {{ formatDate(membership.expires_at) }}</template>
          </p>
        </div>
      </div>
      <div class="member-card-right">
        <div class="balance">
          <span class="balance-label">虚拟余额</span>
          <span class="balance-amount">¥{{ membership.virtual_money?.toFixed(2) || '0.00' }}</span>
        </div>
        <el-button
          v-if="membership.level !== 'max'"
          type="primary"
          @click="showPricing = true"
        >
          {{ membership.level === 'free' ? '升级会员' : '升级方案' }}
        </el-button>
      </div>
    </div>

    <!-- 权益概览 -->
    <div class="section">
      <h3 class="section-title">🎁 我的权益</h3>
      <el-row :gutter="16">
        <el-col :span="8" v-for="benefit in currentBenefits" :key="benefit.label">
          <div class="benefit-card">
            <span class="benefit-icon">{{ benefit.icon }}</span>
            <span class="benefit-label">{{ benefit.label }}</span>
            <span class="benefit-value">{{ benefit.value }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 已安装场景 -->
    <div class="section">
      <div class="section-header">
        <h3 class="section-title">🧩 已安装场景</h3>
        <el-button text type="primary" @click="$router.push('/market')">
          前往模版市场 →
        </el-button>
      </div>
      <div class="installed-scenes">
        <div v-for="scene in installedSceneDetails" :key="scene.id" class="installed-chip">
          <span>{{ scene.icon }}</span>
          <span>{{ scene.title }}</span>
          <el-tag size="small" :type="scene.price_tier === 'free' ? 'success' : scene.price_tier === 'basic' ? '' : 'warning'">
            {{ priceLabel(scene.price_tier) }}
          </el-tag>
        </div>
        <el-empty v-if="installedSceneDetails.length === 0" description="暂无已安装场景" :image-size="60" />
      </div>
    </div>

    <!-- 我的发布（预留） -->
    <div class="section">
      <h3 class="section-title">📤 我的发布</h3>
      <el-empty description="功能开发中，敬请期待" :image-size="60">
        <template #description>
          <p>即将支持：发布自定义模版到模版市场，赚取虚拟金额</p>
        </template>
      </el-empty>
    </div>

    <!-- 最近流水 -->
    <div class="section">
      <h3 class="section-title">📋 交易记录</h3>
      <el-table :data="transactions" stripe style="width: 100%" v-if="transactions.length > 0">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="action" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.action === 'purchase' ? 'primary' : 'success'" size="small">
              {{ row.action === 'purchase' ? '充值' : '激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="详情" />
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.amount > 0 ? '#e6a23c' : '#909399' }">
              {{ row.amount > 0 ? `-¥${row.amount.toFixed(2)}` : '-' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无交易记录" :image-size="60" />
    </div>

    <!-- 激活码兑换 -->
    <div class="section">
      <h3 class="section-title">🔑 激活码兑换</h3>
      <div class="activate-row">
        <el-input v-model="activateCode" placeholder="请输入激活码" clearable style="width: 360px" />
        <el-button type="primary" :loading="activating" @click="handleActivate">兑换</el-button>
      </div>
    </div>

    <!-- 购买方案弹窗 -->
    <el-dialog v-model="showPricing" title="选择方案" width="780px" destroy-on-close>
      <div class="pricing-grid">
        <div
          v-for="plan in purchasablePlans"
          :key="plan.level"
          class="pricing-card"
          :class="{ recommended: plan.level === 'pro' }"
        >
          <div class="pricing-badge" v-if="plan.level === 'pro'">最受欢迎</div>
          <h3>{{ plan.name }}</h3>
          <div class="pricing-price">
            <span class="price-amount">¥{{ plan.price }}</span>
            <span class="price-period">/{{ plan.period }}</span>
          </div>
          <ul class="pricing-features">
            <li v-for="f in plan.features" :key="f">✓ {{ f }}</li>
          </ul>
          <p class="pricing-access">{{ plan.scene_access }}</p>

          <!-- 月数选择 -->
          <div class="months-select">
            <el-radio-group v-model="selectedMonths[plan.level]" size="small">
              <el-radio-button :label="1">1月</el-radio-button>
              <el-radio-button :label="3">3月</el-radio-button>
              <el-radio-button :label="6">6月</el-radio-button>
              <el-radio-button :label="12">12月</el-radio-button>
            </el-radio-group>
            <div class="total-price">
              合计: <strong>¥{{ (plan.price * selectedMonths[plan.level]).toFixed(2) }}</strong>
            </div>
          </div>

          <el-button
            type="primary"
            size="large"
            :loading="purchasing === plan.level"
            @click="handlePurchase(plan.level)"
            style="width: 100%; margin-top: 12px"
          >
            立即开通
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { Membership, PricingPlan, MembershipTransaction, SceneConfig } from '@/api/types'

const membership = ref<Membership>({ user_id: 0, level: 'free', is_expired: false, virtual_money: 0 })
const plans = ref<PricingPlan[]>([])
const transactions = ref<MembershipTransaction[]>([])
const allScenes = ref<SceneConfig[]>([])
const installedSceneIds = ref<string[]>([])
const activateCode = ref('')
const activating = ref(false)
const purchasing = ref('')
const showPricing = ref(false)
const selectedMonths = ref<Record<string, number>>({ pro: 1, max: 1 })

const levelIcon = computed(() => {
  const map: Record<string, string> = { free: '🆓', pro: '⭐', max: '👑' }
  return map[membership.value.level] ?? '🆓'
})

const levelName = computed(() => {
  const map: Record<string, string> = { free: '免费账户', pro: 'Pro 会员', max: 'Max 会员' }
  return map[membership.value.level] ?? '免费账户'
})

const currentBenefits = computed(() => {
  const level = membership.value.level
  const sceneCount = installedSceneIds.value.length
  return [
    { icon: '🧩', label: '可用场景', value: `${sceneCount} 个` },
    { icon: '💰', label: '虚拟余额', value: `¥${(membership.value.virtual_money ?? 0).toFixed(2)}` },
    { icon: '🎯', label: '会员等级', value: levelName.value },
    { icon: '📤', label: '已发布模版', value: '开发中' },
    { icon: '⚡', label: '创作优先级', value: level === 'max' ? '最高' : level === 'pro' ? '优先' : '普通' },
    { icon: '📅', label: '有效期', value: level === 'free' ? '永久' : formatDate(membership.value.expires_at) },
  ]
})

const installedSceneDetails = computed(() => {
  return allScenes.value.filter(s => installedSceneIds.value.includes(s.id))
})

const purchasablePlans = computed(() => {
  const current = membership.value.level
  if (current === 'free') return plans.value.filter(p => p.level !== 'free')
  if (current === 'pro') return plans.value.filter(p => p.level === 'max')
  return []
})

function priceLabel(tier: string): string {
  const map: Record<string, string> = { free: '免费', basic: '基础', premium: '高级' }
  return map[tier] ?? tier
}

function formatDate(date?: string | null): string {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

async function handleActivate() {
  if (!activateCode.value.trim()) return
  activating.value = true
  try {
    membership.value = await api.membership.activate(activateCode.value.trim())
    ElMessage.success('激活成功！')
    activateCode.value = ''
    await loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '激活失败')
  } finally {
    activating.value = false
  }
}

async function handlePurchase(level: string) {
  purchasing.value = level
  try {
    membership.value = await api.membership.purchase(level, selectedMonths.value[level])
    ElMessage.success('开通成功！')
    showPricing.value = false
    await loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '购买失败')
  } finally {
    purchasing.value = ''
  }
}

async function loadData() {
  try {
    const [m, t, ids, scenes] = await Promise.all([
      api.membership.me(),
      api.membership.transactions().catch(() => []),
      api.membership.installedScenes().catch(() => []),
      api.sceneConfigs.list().catch(() => []),
    ])
    membership.value = m
    transactions.value = t
    installedSceneIds.value = ids
    allScenes.value = scenes
  } catch (e) {
    console.error('加载会员信息失败:', e)
  }
}

onMounted(async () => {
  // plans 只加载一次
  try { plans.value = await api.membership.plans() } catch {}
  await loadData()
})
</script>

<style scoped>
.membership-page {
  max-width: 960px;
  margin: 0 auto;
}

/* ── 会员信息卡片 ── */
.member-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 28px 32px;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.member-card.pro {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}
.member-card.max {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}
.member-card-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.level-icon {
  font-size: 48px;
}
.member-info h2 {
  margin: 0 0 4px;
  font-size: 22px;
}
.expire-text {
  margin: 0;
  opacity: 0.85;
  font-size: 14px;
}
.member-card-right {
  display: flex;
  align-items: center;
  gap: 24px;
}
.balance {
  text-align: right;
}
.balance-label {
  display: block;
  font-size: 12px;
  opacity: 0.8;
}
.balance-amount {
  font-size: 28px;
  font-weight: bold;
}

/* ── 区块 ── */
.section {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.section-title {
  margin: 0 0 16px;
  font-size: 16px;
  color: #303133;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header .section-title {
  margin-bottom: 0;
}

/* ── 权益卡片 ── */
.benefit-card {
  background: #f8f9fb;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  margin-bottom: 12px;
}
.benefit-icon {
  display: block;
  font-size: 24px;
  margin-bottom: 6px;
}
.benefit-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.benefit-value {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

/* ── 已安装场景 ── */
.installed-scenes {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.installed-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f4f4f5;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 14px;
}

/* ── 激活码 ── */
.activate-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* ── 购买弹窗 ── */
.pricing-grid {
  display: flex;
  gap: 20px;
}
.pricing-card {
  flex: 1;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  position: relative;
  transition: border-color 0.2s;
}
.pricing-card.recommended {
  border-color: #409eff;
}
.pricing-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: #409eff;
  color: #fff;
  font-size: 12px;
  padding: 2px 14px;
  border-radius: 10px;
}
.pricing-card h3 {
  margin: 0 0 12px;
  font-size: 18px;
}
.pricing-price {
  margin-bottom: 16px;
}
.price-amount {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}
.price-period {
  font-size: 14px;
  color: #909399;
}
.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 12px;
  text-align: left;
  font-size: 13px;
  color: #606266;
}
.pricing-features li {
  padding: 4px 0;
}
.pricing-access {
  font-size: 12px;
  color: #909399;
  margin-bottom: 16px;
}
.months-select {
  margin-top: 12px;
}
.total-price {
  margin-top: 8px;
  font-size: 14px;
  color: #303133;
}
</style>
