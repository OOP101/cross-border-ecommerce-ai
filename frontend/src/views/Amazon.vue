<template>
  <div class="page">
    <!-- 站点选择 -->
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>亚马逊 SP-API 对接</span>
          <el-select v-model="selectedMarketplace" placeholder="选择站点" style="width: 120px">
            <el-option
              v-for="m in marketplaces"
              :key="m.code"
              :label="`${m.code} - ${m.name}`"
              :value="m.code"
            />
          </el-select>
        </div>
      </template>
      
      <el-alert
        title="授权状态"
        :type="isAuthorized ? 'success' : 'warning'"
        :closable="false"
        show-icon
      >
        <template #title>
          {{ isAuthorized ? '已授权' : '未授权' }}
          <el-button 
            v-if="!isAuthorized" 
            type="primary" 
            size="small" 
            @click="startAuth"
            style="margin-left: 12px"
          >
            开始授权
          </el-button>
        </template>
      </el-alert>
    </el-card>

    <!-- 功能标签页 -->
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 订单管理 -->
      <el-tab-pane label="订单管理" name="orders">
        <el-form :inline="true" :model="orderQuery" class="mb-4">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="orderQuery.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="orderQuery.status" placeholder="全部状态">
              <el-option label="全部" value="" />
              <el-option label="待发货" value="Pending" />
              <el-option label="已发货" value="Shipped" />
              <el-option label="已完成" value="Completed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="queryOrders">查询订单</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="orders" v-loading="ordersLoading" stripe>
          <el-table-column prop="order_id" label="订单号" width="180" />
          <el-table-column prop="order_status" label="状态" width="120" />
          <el-table-column prop="order_date" label="下单时间" width="180" />
          <el-table-column prop="amount" label="金额" width="120" />
          <el-table-column prop="currency" label="币种" width="80" />
          <el-table-column label="操作" fixed="right" width="200">
            <template #default="{ row }">
              <el-button size="small" @click="viewOrderDetail(row)">详情</el-button>
              <el-button size="small" type="success" @click="analyzeOrder(row)">AI 分析</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 商品目录 -->
      <el-tab-pane label="商品目录" name="catalog">
        <el-form :inline="true" :model="catalogQuery" class="mb-4">
          <el-form-item label="搜索">
            <el-input 
              v-model="catalogQuery.keywords" 
              placeholder="输入商品名称或 ASIN"
              style="width: 300px"
              @keyup.enter="searchCatalog"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchCatalog">搜索商品</el-button>
          </el-form-item>
        </el-form>

        <el-row :gutter="20">
          <el-col :span="6" v-for="item in catalogItems" :key="item.asin">
            <el-card shadow="hover" class="product-card">
              <img :src="item.image || 'https://via.placeholder.com/200'" class="product-image" />
              <div class="product-info">
                <div class="product-title">{{ item.title }}</div>
                <div class="product-asin">ASIN: {{ item.asin }}</div>
                <div class="product-price">{{ item.price }} {{ item.currency }}</div>
                <el-button size="small" type="primary" @click="generateCopy(item)">
                  生成文案
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 库存管理 -->
      <el-tab-pane label="库存管理" name="inventory">
        <el-button type="primary" @click="queryInventory" class="mb-4">
          刷新库存
        </el-button>

        <el-table :data="inventory" v-loading="inventoryLoading" stripe>
          <el-table-column prop="sku" label="SKU" width="150" />
          <el-table-column prop="asin" label="ASIN" width="150" />
          <el-table-column prop="product_name" label="商品名称" />
          <el-table-column prop="available" label="可用库存" width="120" />
          <el-table-column prop="reserved" label="预留库存" width="120" />
          <el-table-column prop="total" label="总库存" width="120" />
        </el-table>
      </el-tab-pane>

      <!-- AI 联动 -->
      <el-tab-pane label="AI 联动" name="ai">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>订单智能分析</span>
              </template>
              <p>基于最近订单数据，AI 自动生成销售分析报告</p>
              <el-form :inline="true">
                <el-form-item label="分析天数">
                  <el-input-number v-model="aiAnalysis.days" :min="1" :max="90" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="runOrderAnalysis" :loading="aiAnalysis.loading">
                    开始分析
                  </el-button>
                </el-form-item>
              </el-form>
              
              <el-alert
                v-if="aiAnalysis.result"
                type="success"
                :closable="false"
                class="mt-4"
              >
                <template #title>
                  <div v-html="aiAnalysis.result.replace(/\n/g, '<br>')"></div>
                </template>
              </el-alert>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                <span>热销商品文案生成</span>
              </template>
              <p>从热销订单中提取商品，自动生成多语言营销文案</p>
              <el-form :inline="true">
                <el-form-item label="Top N">
                  <el-input-number v-model="hotProducts.topN" :min="1" :max="20" />
                </el-form-item>
                <el-form-item label="目标语言">
                  <el-select v-model="hotProducts.language">
                    <el-option label="英语" value="en" />
                    <el-option label="日语" value="ja" />
                    <el-option label="德语" value="de" />
                    <el-option label="法语" value="fr" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="generateHotProductsCopy" :loading="hotProducts.loading">
                    生成文案
                  </el-button>
                </el-form-item>
              </el-form>

              <el-alert
                v-if="hotProducts.result"
                type="success"
                :closable="false"
                class="mt-4"
              >
                <template #title>
                  <div v-html="hotProducts.result.replace(/\n/g, '<br>')"></div>
                </template>
              </el-alert>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const selectedMarketplace = ref('US')
const isAuthorized = ref(false)
const activeTab = ref('orders')

// 市场列表
const marketplaces = ref([
  { code: 'US', name: '美国' },
  { code: 'UK', name: '英国' },
  { code: 'DE', name: '德国' },
  { code: 'FR', name: '法国' },
  { code: 'JP', name: '日本' },
  { code: 'CA', name: '加拿大' },
  { code: 'AU', name: '澳大利亚' },
])

// 订单查询
const orderQuery = ref({
  dateRange: [],
  status: '',
})
const orders = ref([])
const ordersLoading = ref(false)

// 商品目录
const catalogQuery = ref({
  keywords: '',
})
const catalogItems = ref([])

// 库存管理
const inventory = ref([])
const inventoryLoading = ref(false)

// AI 分析
const aiAnalysis = ref({
  days: 7,
  loading: false,
  result: '',
})

const hotProducts = ref({
  topN: 5,
  language: 'en',
  loading: false,
  result: '',
})

// 开始授权
const startAuth = async () => {
  try {
    const res = await api.get('/amazon/oauth/authorize')
    if (res.authorization_url) {
      window.open(res.authorization_url, '_blank')
      ElMessage.success('已打开授权页面，请完成授权')
    }
  } catch (error) {
    ElMessage.error('获取授权链接失败')
  }
}

// 查询订单
const queryOrders = async () => {
  ordersLoading.value = true
  try {
    const params = {
      marketplace: selectedMarketplace.value,
    }
    if (orderQuery.value.dateRange?.length === 2) {
      params.created_after = orderQuery.value.dateRange[0]
      params.created_before = orderQuery.value.dateRange[1]
    }
    if (orderQuery.value.status) {
      params.order_statuses = orderQuery.value.status
    }
    
    const res = await api.get('/amazon/orders', { params })
    orders.value = res.orders || []
  } catch (error) {
    ElMessage.error('查询订单失败')
  } finally {
    ordersLoading.value = false
  }
}

// 查看订单详情
const viewOrderDetail = (order) => {
  ElMessage.info(`查看订单 ${order.order_id} 详情`)
}

// AI 分析订单
const analyzeOrder = async (order) => {
  try {
    const res = await api.get(`/amazon/ai/analyze-orders`, {
      params: {
        marketplace: selectedMarketplace.value,
        days: 7,
      }
    })
    ElMessage.success('AI 分析完成')
    console.log('AI 分析结果:', res)
  } catch (error) {
    ElMessage.error('AI 分析失败')
  }
}

// 搜索商品
const searchCatalog = async () => {
  if (!catalogQuery.value.keywords) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  try {
    const res = await api.get('/amazon/catalog/search', {
      params: {
        keywords: catalogQuery.value.keywords,
        marketplace: selectedMarketplace.value,
      }
    })
    catalogItems.value = res.items || []
  } catch (error) {
    ElMessage.error('搜索商品失败')
  }
}

// 生成商品文案
const generateCopy = async (item) => {
  try {
    const res = await api.post('/copywriting/generate', {
      product_name: item.title,
      category: 'amazon',
      target_market: selectedMarketplace.value,
      target_language: 'en',
      style: 'professional',
    })
    ElMessage.success('文案生成成功')
    console.log('生成的文案:', res)
  } catch (error) {
    ElMessage.error('文案生成失败')
  }
}

// 查询库存
const queryInventory = async () => {
  inventoryLoading.value = true
  try {
    const res = await api.get('/amazon/inventory/summary', {
      params: {
        marketplace: selectedMarketplace.value,
      }
    })
    inventory.value = res.inventory || []
  } catch (error) {
    ElMessage.error('查询库存失败')
  } finally {
    inventoryLoading.value = false
  }
}

// 运行订单分析
const runOrderAnalysis = async () => {
  aiAnalysis.value.loading = true
  try {
    const res = await api.get('/amazon/ai/analyze-orders', {
      params: {
        marketplace: selectedMarketplace.value,
        days: aiAnalysis.value.days,
      }
    })
    aiAnalysis.value.result = res.analysis || '分析完成'
    ElMessage.success('分析完成')
  } catch (error) {
    ElMessage.error('分析失败')
  } finally {
    aiAnalysis.value.loading = false
  }
}

// 生成热销商品文案
const generateHotProductsCopy = async () => {
  hotProducts.value.loading = true
  try {
    const res = await api.post('/amazon/ai/generate-copy-from-orders', {
      marketplace: selectedMarketplace.value,
      days: 7,
      top_n: hotProducts.value.topN,
      target_language: hotProducts.value.language,
    })
    hotProducts.value.result = res.copy || '文案生成完成'
    ElMessage.success('文案生成完成')
  } catch (error) {
    ElMessage.error('文案生成失败')
  } finally {
    hotProducts.value.loading = false
  }
}

onMounted(() => {
  // 检查授权状态
  // TODO: 实现授权状态检查接口
})
</script>

<style scoped>
.page {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-card {
  margin-bottom: 20px;
}

.product-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  margin-bottom: 12px;
}

.product-info {
  padding: 8px;
}

.product-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.product-asin {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.product-price {
  font-size: 16px;
  font-weight: bold;
  color: #ff6600;
  margin-bottom: 12px;
}
</style>
