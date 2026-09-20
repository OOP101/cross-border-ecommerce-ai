<template>
  <div class="page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">总客户数</div>
            <div class="stat-value">{{ stats.total || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">A 级客户</div>
            <div class="stat-value">{{ stats.grade_a || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">待跟进</div>
            <div class="stat-value">{{ stats.pending_follow_up || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">
            <div class="stat-label">本月新增</div>
            <div class="stat-value">{{ stats.month_new || 0 }}</div>
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
            placeholder="搜索客户名称、联系人、邮箱..."
            clearable
            @keyup.enter="loadCustomers"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建客户
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 客户列表 -->
    <el-card>
      <el-table :data="customers" v-loading="loading" stripe>
        <el-table-column prop="company_name" label="客户名称" min-width="200" />
        <el-table-column prop="contact_person" label="联系人" width="120" />
        <el-table-column prop="email" label="邮箱" width="180" />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column prop="grade" label="等级" width="80">
          <template #default="{ row }">
            <el-tag :type="getGradeType(row.grade)">{{ row.grade }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewCustomer(row)">详情</el-button>
            <el-button size="small" type="primary" @click="showFollowUpDialog(row)">跟进</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadCustomers"
        @current-change="loadCustomers"
        class="mt-4"
      />
    </el-card>

    <!-- 新建客户对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建客户" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="客户名称" required>
          <el-input v-model="createForm.company_name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="createForm.contact_person" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="createForm.email" type="email" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="createForm.phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="createForm.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="行业">
          <el-input v-model="createForm.industry" />
        </el-form-item>
        <el-form-item label="客户等级">
          <el-select v-model="createForm.grade">
            <el-option label="A 级" value="A" />
            <el-option label="B 级" value="B" />
            <el-option label="C 级" value="C" />
            <el-option label="D 级" value="D" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="createForm.source" clearable>
            <el-option label="亚马逊" value="amazon" />
            <el-option label="展会" value="exhibition" />
            <el-option label="官网" value="website" />
            <el-option label="转介绍" value="referral" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createCustomer" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 客户详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="客户详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="客户名称">{{ detailData.company_name }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ detailData.contact_person }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ detailData.email }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ detailData.phone }}</el-descriptions-item>
        <el-descriptions-item label="地址" :span="2">{{ detailData.address }}</el-descriptions-item>
        <el-descriptions-item label="行业">{{ detailData.industry }}</el-descriptions-item>
        <el-descriptions-item label="等级">
          <el-tag :type="getGradeType(detailData.grade)">{{ detailData.grade }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="来源">{{ detailData.source }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(detailData.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detailData.notes }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>跟进记录</el-divider>

      <el-timeline>
        <el-timeline-item
          v-for="item in followUps"
          :key="item.id"
          :timestamp="formatTime(item.created_at)"
          placement="top"
        >
          <el-card>
            <div><strong>{{ getContactTypeLabel(item.contact_type) }}</strong></div>
            <div>{{ item.content }}</div>
            <div v-if="item.next_follow_date" class="next-follow">
              下次跟进：{{ formatTime(item.next_follow_date) }}
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="showFollowUpDialog(detailData)">新增跟进</el-button>
      </template>
    </el-dialog>

    <!-- 跟进记录对话框 -->
    <el-dialog v-model="followUpDialogVisible" title="新增跟进记录" width="500px">
      <el-form :model="followUpForm" label-width="100px">
        <el-form-item label="联系方式" required>
          <el-select v-model="followUpForm.contact_type">
            <el-option label="电话" value="phone" />
            <el-option label="邮件" value="email" />
            <el-option label="面谈" value="meeting" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="跟进内容" required>
          <el-input v-model="followUpForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="下次跟进">
          <el-date-picker
            v-model="followUpForm.next_follow_date"
            type="datetime"
            placeholder="选择日期时间"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="followUpDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createFollowUp" :loading="creatingFollowUp">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import api from '../api'

// 统计数据
const stats = ref({})

// 客户列表
const customers = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

// 新建客户
const createDialogVisible = ref(false)
const creating = ref(false)
const createForm = ref({
  company_name: '',
  contact_person: '',
  email: '',
  phone: '',
  address: '',
  industry: '',
  grade: 'C',
  source: '',
  notes: '',
})

// 客户详情
const detailDialogVisible = ref(false)
const detailData = ref({})
const followUps = ref([])

// 跟进记录
const followUpDialogVisible = ref(false)
const creatingFollowUp = ref(false)
const followUpForm = ref({
  customer_id: null,
  contact_type: 'phone',
  content: '',
  next_follow_date: null,
})

// 加载统计数据
const loadStats = async () => {
  try {
    stats.value = await api.get('/crm/stats/overview')
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

// 加载客户列表
const loadCustomers = async () => {
  loading.value = true
  try {
    const res = await api.get('/crm/customers', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        keyword: searchKeyword.value || undefined,
      },
    })
    customers.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('加载客户列表失败')
  } finally {
    loading.value = false
  }
}

// 显示新建对话框
const showCreateDialog = () => {
  createForm.value = {
    company_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    industry: '',
    grade: 'C',
    source: '',
    notes: '',
  }
  createDialogVisible.value = true
}

// 创建客户
const createCustomer = async () => {
  if (!createForm.value.company_name) {
    ElMessage.warning('请输入客户名称')
    return
  }

  creating.value = true
  try {
    await api.post('/crm/customers', createForm.value)
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    loadCustomers()
    loadStats()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

// 查看客户详情
const viewCustomer = async (row) => {
  try {
    detailData.value = await api.get(`/crm/customers/${row.id}`)
    followUps.value = await api.get(`/crm/customers/${row.id}/follow-ups`)
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载详情失败')
  }
}

// 显示跟进对话框
const showFollowUpDialog = (row) => {
  followUpForm.value = {
    customer_id: row.id,
    contact_type: 'phone',
    content: '',
    next_follow_date: null,
  }
  followUpDialogVisible.value = true
}

// 创建跟进记录
const createFollowUp = async () => {
  if (!followUpForm.value.content) {
    ElMessage.warning('请输入跟进内容')
    return
  }

  creatingFollowUp.value = true
  try {
    await api.post('/crm/follow-ups', followUpForm.value)
    ElMessage.success('跟进记录已保存')
    followUpDialogVisible.value = false
    
    // 刷新详情
    if (detailDialogVisible.value) {
      followUps.value = await api.get(`/crm/customers/${detailData.value.id}/follow-ups`)
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    creatingFollowUp.value = false
  }
}

// 辅助函数
const getGradeType = (grade) => {
  const map = { A: 'danger', B: 'warning', C: 'info', D: '' }
  return map[grade] || ''
}

const getContactTypeLabel = (type) => {
  const map = { phone: '电话', email: '邮件', meeting: '面谈', other: '其他' }
  return map[type] || type
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadStats()
  loadCustomers()
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

.next-follow {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}
</style>
