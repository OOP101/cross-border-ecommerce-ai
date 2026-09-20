<template>
  <div class="page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">总商品数</div>
            <div class="stat-value">{{ stats.total || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">在售商品</div>
            <div class="stat-value">{{ stats.active || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">低库存</div>
            <div class="stat-value">{{ stats.low_stock || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">库存总值</div>
            <div class="stat-value">¥{{ formatMoney(stats.total_value) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索和操作栏 -->
    <el-card class="mb-4">
      <el-row :gutter="20" align="middle">
        <el-col :span="18">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索商品名称、SKU、ASIN..."
            clearable
            @keyup.enter="loadProducts"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建商品
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 商品列表 -->
    <el-card>
      <el-table :data="products" v-loading="loading" stripe>
        <el-table-column prop="name" label="商品名称" min-width="200" />
        <el-table-column prop="sku" label="SKU" width="120" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column label="价格" width="120">
          <template #default="{ row }">
            {{ row.currency }} {{ row.selling_price }}
          </template>
        </el-table-column>
        <el-table-column prop="stock_quantity" label="库存" width="100">
          <template #default="{ row }">
            <el-tag :type="row.stock_quantity < 10 ? 'danger' : 'success'">
              {{ row.stock_quantity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amazon_asin" label="ASIN" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '在售' : '下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewProduct(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editProduct(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadProducts"
        @current-change="loadProducts"
        class="mt-4"
      />
    </el-card>

    <!-- 新建/编辑商品对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑商品' : '新建商品'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="SKU" required>
              <el-input v-model="form.sku" :disabled="isEdit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="商品名称" required>
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="分类">
              <el-input v-model="form.category" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌">
              <el-input v-model="form.brand" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="成本价">
              <el-input-number v-model="form.cost_price" :min="0" :precision="2" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="售价">
              <el-input-number v-model="form.selling_price" :min="0" :precision="2" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="币种">
              <el-select v-model="form.currency">
                <el-option label="USD" value="USD" />
                <el-option label="EUR" value="EUR" />
                <el-option label="GBP" value="GBP" />
                <el-option label="JPY" value="JPY" />
                <el-option label="CNY" value="CNY" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="库存数量">
              <el-input-number v-model="form.stock_quantity" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status">
                <el-option label="在售" value="active" />
                <el-option label="下架" value="inactive" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="亚马逊 ASIN">
              <el-input v-model="form.amazon_asin" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="亚马逊站点">
              <el-select v-model="form.amazon_marketplace" clearable>
                <el-option label="美国" value="US" />
                <el-option label="英国" value="UK" />
                <el-option label="德国" value="DE" />
                <el-option label="日本" value="JP" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProduct" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 商品详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="商品详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="商品名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="SKU">{{ detailData.sku }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ detailData.category }}</el-descriptions-item>
        <el-descriptions-item label="品牌">{{ detailData.brand }}</el-descriptions-item>
        <el-descriptions-item label="成本价">{{ detailData.currency }} {{ detailData.cost_price }}</el-descriptions-item>
        <el-descriptions-item label="售价">{{ detailData.currency }} {{ detailData.selling_price }}</el-descriptions-item>
        <el-descriptions-item label="库存">
          <el-tag :type="detailData.stock_quantity < 10 ? 'danger' : 'success'">
            {{ detailData.stock_quantity }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detailData.status === 'active' ? 'success' : 'info'">
            {{ detailData.status === 'active' ? '在售' : '下架' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="亚马逊 ASIN">{{ detailData.amazon_asin }}</el-descriptions-item>
        <el-descriptions-item label="亚马逊站点">{{ detailData.amazon_marketplace }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ detailData.description }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(detailData.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(detailData.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="editProduct(detailData)">编辑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import api from '../api'

// 统计数据
const stats = ref({})

// 商品列表
const products = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

// 新建/编辑
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = ref({
  sku: '',
  name: '',
  category: '',
  brand: '',
  description: '',
  cost_price: 0,
  selling_price: 0,
  currency: 'USD',
  stock_quantity: 0,
  amazon_asin: '',
  amazon_marketplace: '',
  status: 'active',
})

// 详情
const detailDialogVisible = ref(false)
const detailData = ref({})

// 加载统计数据
const loadStats = async () => {
  try {
    stats.value = await api.get('/products/stats/overview')
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

// 加载商品列表
const loadProducts = async () => {
  loading.value = true
  try {
    const res = await api.get('/products', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        keyword: searchKeyword.value || undefined,
      },
    })
    products.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('加载商品列表失败')
  } finally {
    loading.value = false
  }
}

// 显示新建对话框
const showCreateDialog = () => {
  isEdit.value = false
  form.value = {
    sku: '',
    name: '',
    category: '',
    brand: '',
    description: '',
    cost_price: 0,
    selling_price: 0,
    currency: 'USD',
    stock_quantity: 0,
    amazon_asin: '',
    amazon_marketplace: '',
    status: 'active',
  }
  dialogVisible.value = true
}

// 编辑商品
const editProduct = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

// 保存商品
const saveProduct = async () => {
  if (!form.value.sku || !form.value.name) {
    ElMessage.warning('请填写 SKU 和商品名称')
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await api.put(`/products/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/products', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadProducts()
    loadStats()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 查看详情
const viewProduct = async (row) => {
  try {
    detailData.value = await api.get(`/products/${row.id}`)
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载详情失败')
  }
}

// 辅助函数
const formatMoney = (value) => {
  if (!value) return '0.00'
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadStats()
  loadProducts()
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

.stat {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}
</style>
