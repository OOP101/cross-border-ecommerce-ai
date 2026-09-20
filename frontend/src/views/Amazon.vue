<template>
  <div class="page">
    <!-- 顶部状态栏 -->
    <div class="status-bar">
      <div class="status-left">
        <div class="status-dot" :class="isAuthorized ? 'online' : 'offline'"></div>
        <span class="status-text">{{ isAuthorized ? '已连接' : '未连接' }}</span>
        <el-tag v-if="isMockMode" size="small" effect="plain" round>Mock</el-tag>
      </div>
      <div class="status-right">
        <el-segmented v-model="selectedMarketplace" :options="marketplaceOptions" size="small" />
      </div>
    </div>

    <!-- 功能标签页 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 订单管理 -->
      <el-tab-pane name="orders">
        <template #label>
          <div class="tab-label">
            <span class="tab-icon">📦</span>
            <span>订单</span>
            <span v-if="orders.length" class="tab-badge">{{ orders.length }}</span>
          </div>
        </template>

        <!-- 筛选栏 -->
        <div class="filter-bar">
          <el-date-picker
            v-model="orderQuery.dateRange"
            type="daterange"
            range-separator="–"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            size="default"
            style="width: 260px"
          />
          <el-select v-model="orderQuery.status" placeholder="状态" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="待发货" value="Pending" />
            <el-option label="已发货" value="Shipped" />
            <el-option label="已完成" value="Completed" />
          </el-select>
          <el-button type="primary" @click="queryOrders" :loading="ordersLoading" round>
            查询
          </el-button>
        </div>

        <!-- 订单列表 -->
        <el-table :data="orders" v-loading="ordersLoading" stripe class="order-table">
          <el-table-column prop="AmazonOrderId" label="订单号" min-width="180">
            <template #default="{ row }">
              <span class="order-id">{{ row.AmazonOrderId }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="OrderStatus" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.OrderStatus)" size="small" round effect="light">
                {{ statusLabel(row.OrderStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="PurchaseDate" label="时间" width="170">
            <template #default="{ row }">
              <span class="text-secondary">{{ formatTime(row.PurchaseDate) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="130" align="right">
            <template #default="{ row }">
              <span class="amount">{{ row.OrderTotal?.Amount || '–' }} {{ row.OrderTotal?.CurrencyCode || '' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click="viewOrderDetail(row)">详情</el-button>
              <el-button 
                size="small" 
                text 
                type="success" 
                :loading="analyzingOrderId === row.AmazonOrderId"
                @click="analyzeOrder(row)"
              >
                {{ analyzingOrderId === row.AmazonOrderId ? '分析中…' : 'AI 分析' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 商品目录 -->
      <el-tab-pane name="catalog">
        <template #label>
          <div class="tab-label">
            <span class="tab-icon">📋</span>
            <span>商品</span>
          </div>
        </template>

        <div class="filter-bar">
          <el-input
            v-model="catalogQuery.keywords"
            placeholder="搜索商品名称或 ASIN…"
            clearable
            style="width: 320px"
            @keyup.enter="searchCatalog"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="searchCatalog" round>搜索</el-button>
        </div>

        <el-row :gutter="16">
          <el-col :span="6" v-for="item in catalogItems" :key="item.asin">
            <div class="product-card">
              <img :src="item.image || 'https://via.placeholder.com/200'" class="product-image" />
              <div class="product-body">
                <div class="product-title">{{ item.title }}</div>
                <div class="product-meta">ASIN: {{ item.asin }}</div>
                <div class="product-price">{{ item.price }} {{ item.currency }}</div>
                <el-button size="small" type="primary" round @click="generateCopy(item)">生成文案</el-button>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 库存管理 -->
      <el-tab-pane name="inventory">
        <template #label>
          <div class="tab-label">
            <span class="tab-icon">📊</span>
            <span>库存</span>
          </div>
        </template>

        <div class="filter-bar">
          <el-button type="primary" @click="queryInventory" :loading="inventoryLoading" round>
            刷新库存
          </el-button>
        </div>

        <el-table :data="inventory" v-loading="inventoryLoading" stripe>
          <el-table-column prop="sku" label="SKU" width="150" />
          <el-table-column prop="asin" label="ASIN" width="150" />
          <el-table-column prop="product_name" label="商品名称" />
          <el-table-column prop="available" label="可用" width="100" align="right" />
          <el-table-column prop="reserved" label="预留" width="100" align="right" />
          <el-table-column prop="total" label="总计" width="100" align="right">
            <template #default="{ row }">
              <el-tag :type="row.total < 10 ? 'danger' : 'success'" size="small" round>
                {{ row.total }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- AI 联动 -->
      <el-tab-pane name="ai">
        <template #label>
          <div class="tab-label">
            <span class="tab-icon">✨</span>
            <span>AI</span>
            <span v-if="aiAnalysis.loading || hotProducts.loading" class="tab-pulse"></span>
          </div>
        </template>

        <el-row :gutter="20">
          <!-- 订单智能分析 -->
          <el-col :span="12">
            <div class="ai-card">
              <div class="ai-card-header">
                <span class="ai-icon">🔍</span>
                <span class="ai-title">订单智能分析</span>
              </div>
              <p class="ai-desc">基于最近订单数据，AI 自动生成销售分析报告</p>
              <div class="ai-controls">
                <div class="ai-control-item">
                  <span class="ai-control-label">分析天数</span>
                  <el-input-number v-model="aiAnalysis.days" :min="1" :max="90" size="small" />
                </div>
                <el-button 
                  type="primary" 
                  @click="runOrderAnalysis" 
                  :loading="aiAnalysis.loading" 
                  round
                >
                  {{ aiAnalysis.loading ? '分析中…' : '开始分析' }}
                </el-button>
              </div>

              <!-- 加载状态 -->
              <div v-if="aiAnalysis.loading" class="ai-loading-state">
                <div class="ai-loading-dots">
                  <span></span><span></span><span></span>
                </div>
                <span>AI 正在分析订单数据…</span>
              </div>

              <!-- 结果展示 -->
              <div v-if="aiAnalysis.result && !aiAnalysis.loading" class="ai-result">
                <div class="ai-result-content" v-html="formatResult(aiAnalysis.result)"></div>
                <el-button size="small" text type="primary" @click="copyText(aiAnalysis.result)">
                  复制结果
                </el-button>
              </div>
            </div>
          </el-col>

          <!-- 热销商品文案 -->
          <el-col :span="12">
            <div class="ai-card">
              <div class="ai-card-header">
                <span class="ai-icon">🔥</span>
                <span class="ai-title">热销商品文案生成</span>
              </div>
              <p class="ai-desc">从热销订单中提取商品，自动生成多语言营销文案</p>
              <div class="ai-controls">
                <div class="ai-control-item">
                  <span class="ai-control-label">Top N</span>
                  <el-input-number v-model="hotProducts.topN" :min="1" :max="20" size="small" />
                </div>
                <div class="ai-control-item">
                  <span class="ai-control-label">语言</span>
                  <el-select v-model="hotProducts.language" size="small">
                    <el-option label="英语" value="en" />
                    <el-option label="日语" value="ja" />
                    <el-option label="德语" value="de" />
                    <el-option label="法语" value="fr" />
                  </el-select>
                </div>
                <el-button 
                  type="primary" 
                  @click="generateHotProductsCopy" 
                  :loading="hotProducts.loading" 
                  round
                >
                  {{ hotProducts.loading ? '生成中…' : '生成文案' }}
                </el-button>
              </div>

              <!-- 加载状态 -->
              <div v-if="hotProducts.loading" class="ai-loading-state">
                <div class="ai-loading-dots">
                  <span></span><span></span><span></span>
                </div>
                <span>AI 正在生成文案…</span>
              </div>

              <!-- 结果展示 -->
              <div v-if="hotProducts.result && !hotProducts.loading" class="ai-result">
                <div class="ai-result-content" v-html="formatResult(hotProducts.result)"></div>
                <el-button size="small" text type="primary" @click="copyText(hotProducts.result)">
                  复制结果
                </el-button>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>

    <!-- 订单详情抽屉 -->
    <el-drawer v-model="orderDetailVisible" title="订单详情" size="400px">
      <template v-if="currentOrder">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单号">{{ currentOrder.AmazonOrderId }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(currentOrder.OrderStatus)" size="small" round>
              {{ statusLabel(currentOrder.OrderStatus) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatTime(currentOrder.PurchaseDate) }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ currentOrder.OrderTotal?.Amount }} {{ currentOrder.OrderTotal?.CurrencyCode }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 20px">
          <el-button type="success" round @click="analyzeOrder(currentOrder)" :loading="analyzingOrderId === currentOrder.AmazonOrderId">
            {{ analyzingOrderId === currentOrder.AmazonOrderId ? 'AI 分析中…' : 'AI 分析此订单' }}
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '../api'

const selectedMarketplace = ref('US')
const isAuthorized = ref(false)
const isMockMode = ref(false)
const activeTab = ref('orders')

// 站点选项（分段控制器）
const marketplaceOptions = [
  { label: '🇺🇸 美国', value: 'US' },
  { label: '🇬🇧 英国', value: 'UK' },
  { label: '🇩🇪 德国', value: 'DE' },
  { label: '🇯🇵 日本', value: 'JP' },
]

// 订单
const orderQuery = ref({ dateRange: [], status: '' })
const orders = ref([])
const ordersLoading = ref(false)
const analyzingOrderId = ref('') // 当前正在分析的订单ID

// 订单详情抽屉
const orderDetailVisible = ref(false)
const currentOrder = ref(null)

// 商品目录
const catalogQuery = ref({ keywords: '' })
const catalogItems = ref([])

// 库存
const inventory = ref([])
const inventoryLoading = ref(false)

// AI 分析
const aiAnalysis = ref({ days: 7, loading: false, result: '' })
const hotProducts = ref({ topN: 5, language: 'en', loading: false, result: '' })

// 工具函数
const statusType = (status) => {
  const map = { Pending: 'warning', Shipped: '', Completed: 'success', Canceled: 'danger' }
  return map[status] || 'info'
}
const statusLabel = (status) => {
  const map = { Pending: '待发货', Shipped: '已发货', Completed: '已完成', Canceled: '已取消' }
  return map[status] || status
}
const formatTime = (dateStr) => {
  if (!dateStr) return '–'
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
const formatResult = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}
const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 授权
const startAuth = async () => {
  try {
    const res = await api.get('/amazon/oauth/authorize')
    if (res.authorization_url) window.open(res.authorization_url, '_blank')
  } catch {
    ElMessage.error('获取授权链接失败')
  }
}

// 订单查询
const queryOrders = async () => {
  ordersLoading.value = true
  try {
    const params = { marketplace: selectedMarketplace.value }
    if (orderQuery.value.dateRange?.length === 2) {
      params.created_after = orderQuery.value.dateRange[0]
      params.created_before = orderQuery.value.dateRange[1]
    }
    if (orderQuery.value.status) params.order_statuses = orderQuery.value.status
    const res = await api.get('/amazon/orders', { params })
    orders.value = res.orders || []
  } catch {
    ElMessage.error('查询订单失败')
  } finally {
    ordersLoading.value = false
  }
}

// 订单详情
const viewOrderDetail = (order) => {
  currentOrder.value = order
  orderDetailVisible.value = true
}

// AI 分析订单
const analyzeOrder = async (order) => {
  analyzingOrderId.value = order.AmazonOrderId
  aiAnalysis.value.loading = true
  aiAnalysis.value.result = ''
  try {
    const res = await api.get('/amazon/ai/analyze-orders', {
      params: { marketplace: selectedMarketplace.value, days: 7 }
    })
    aiAnalysis.value.result = res.analysis || '分析完成'
    activeTab.value = 'ai'
    ElMessage.success('AI 分析完成')
  } catch {
    ElMessage.error('AI 分析失败')
  } finally {
    analyzingOrderId.value = ''
    aiAnalysis.value.loading = false
  }
}

// 商品搜索
const searchCatalog = async () => {
  if (!catalogQuery.value.keywords) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  try {
    const res = await api.get('/amazon/catalog/search', {
      params: { keywords: catalogQuery.value.keywords, marketplace: selectedMarketplace.value }
    })
    catalogItems.value = res.items || []
  } catch {
    ElMessage.error('搜索商品失败')
  }
}

// 生成文案
const generateCopy = async (item) => {
  try {
    await api.post('/copywriting/generate', {
      product_name: item.title,
      category: 'amazon',
      target_market: selectedMarketplace.value,
      target_language: 'en',
      style: 'professional',
    })
    ElMessage.success('文案已生成')
  } catch {
    ElMessage.error('文案生成失败')
  }
}

// 库存查询
const queryInventory = async () => {
  inventoryLoading.value = true
  try {
    const res = await api.get('/amazon/inventory/summary', {
      params: { marketplace: selectedMarketplace.value }
    })
    inventory.value = res.inventory || []
  } catch {
    ElMessage.error('查询库存失败')
  } finally {
    inventoryLoading.value = false
  }
}

// AI 分析
const runOrderAnalysis = async () => {
  aiAnalysis.value.loading = true
  aiAnalysis.value.result = ''
  try {
    const res = await api.get('/amazon/ai/analyze-orders', {
      params: { marketplace: selectedMarketplace.value, days: aiAnalysis.value.days }
    })
    aiAnalysis.value.result = res.analysis || '分析完成'
    ElMessage.success('分析完成')
  } catch {
    ElMessage.error('分析失败')
  } finally {
    aiAnalysis.value.loading = false
  }
}

const generateHotProductsCopy = async () => {
  hotProducts.value.loading = true
  hotProducts.value.result = ''
  try {
    const res = await api.post('/amazon/ai/generate-copy-from-orders', {
      marketplace: selectedMarketplace.value,
      days: 7,
      top_n: hotProducts.value.topN,
      target_language: hotProducts.value.language,
    })
    hotProducts.value.result = res.copy || '文案生成完成'
    ElMessage.success('文案生成完成')
  } catch {
    ElMessage.error('文案生成失败')
  } finally {
    hotProducts.value.loading = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get('/amazon/oauth/authorize')
    if (res.authorization_url?.includes('mock')) {
      isMockMode.value = true
      isAuthorized.value = true
    }
  } catch {}
  queryOrders()
  catalogQuery.value.keywords = 'headphones'
  searchCatalog()
  queryInventory()
})
</script>

<style scoped>
.page {
  padding: 20px;
}

/* 顶部状态栏 */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.status-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-dot.online {
  background: #34c759;
  box-shadow: 0 0 6px rgba(52, 199, 89, 0.4);
}
.status-dot.offline {
  background: #ff9500;
}
.status-text {
  font-size: 14px;
  font-weight: 500;
  color: #1d1d1f;
}

/* 标签页 */
.main-tabs :deep(.el-tabs__header) {
  border-radius: 12px 12px 0 0;
}
.main-tabs :deep(.el-tabs__content) {
  padding: 20px;
}
.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
}
.tab-icon {
  font-size: 16px;
}
.tab-badge {
  background: #007aff;
  color: #fff;
  font-size: 11px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
}
.tab-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34c759;
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

/* 订单表格 */
.order-table .order-id {
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #007aff;
}
.text-secondary {
  color: #86868b;
  font-size: 13px;
}
.amount {
  font-weight: 600;
  color: #1d1d1f;
}

/* 商品卡片 */
.product-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #f0f0f0;
}
.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.product-image {
  width: 100%;
  height: 160px;
  object-fit: cover;
}
.product-body {
  padding: 12px;
}
.product-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d1d1f;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}
.product-meta {
  font-size: 12px;
  color: #86868b;
  margin-bottom: 8px;
}
.product-price {
  font-size: 18px;
  font-weight: 700;
  color: #ff6600;
  margin-bottom: 12px;
}

/* AI 卡片 */
.ai-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
}
.ai-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ai-icon {
  font-size: 24px;
}
.ai-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
}
.ai-desc {
  font-size: 13px;
  color: #86868b;
  margin-bottom: 16px;
}
.ai-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.ai-control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ai-control-label {
  font-size: 13px;
  color: #86868b;
}

/* AI 加载状态 */
.ai-loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
  color: #86868b;
  font-size: 14px;
}
.ai-loading-dots {
  display: flex;
  gap: 4px;
}
.ai-loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #007aff;
  animation: bounce 1.4s ease-in-out infinite;
}
.ai-loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.ai-loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* AI 结果 */
.ai-result {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f4f8 100%);
  border-radius: 12px;
  border: 1px solid #e0e7ee;
}
.ai-result-content {
  font-size: 14px;
  line-height: 1.7;
  color: #1d1d1f;
  margin-bottom: 12px;
  max-height: 300px;
  overflow-y: auto;
}
</style>
