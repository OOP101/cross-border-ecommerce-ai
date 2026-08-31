<template>
  <div class="page">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card header="上传知识文档">
          <el-upload
            drag
            :auto-upload="false"
            :on-change="onFileChange"
            :limit="1"
            accept=".txt,.md,.csv,.pdf,.docx"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或<em>点击选择</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF / Word / Excel / Markdown / TXT</div>
            </template>
          </el-upload>
          <el-button type="primary" :loading="uploading" style="margin-top: 12px; width: 100%" @click="upload">
            上传并向量化
          </el-button>
        </el-card>

        <el-card header="知识库检索" style="margin-top: 20px">
          <el-input v-model="query" placeholder="输入检索关键词" @keydown.enter="search" />
          <el-button type="primary" style="margin-top: 12px; width: 100%" @click="search">检索</el-button>
          <div v-if="searchResults.length" class="search-results">
            <div v-for="(r, i) in searchResults" :key="i" class="sr-item">
              <div class="sr-head">
                <el-tag size="small" type="success" effect="plain">{{ r.metadata?.source || r.source || '未知' }}</el-tag>
                <span class="score">相似度 {{ (r.score * 100).toFixed(1) }}%</span>
              </div>
              <p>{{ r.text }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card header="知识文档列表">
          <el-table :data="documents" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="filename" label="文件名" min-width="200" />
            <el-table-column prop="chunk_count" label="分块数" width="90" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'indexed' ? 'success' : 'info'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="180" />
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button type="danger" size="small" link @click="remove(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const file = ref(null)
const uploading = ref(false)
const documents = ref([])
const query = ref('')
const searchResults = ref([])

const loadDocs = async () => {
  const res = await api.get('/knowledge')
  documents.value = res.documents
}

const onFileChange = (uploadFile) => {
  file.value = uploadFile.raw
}

const upload = async () => {
  if (!file.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    await api.post('/knowledge/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    ElMessage.success('上传并向量化成功')
    file.value = null
    loadDocs()
  } finally {
    uploading.value = false
  }
}

const remove = async (row) => {
  await ElMessageBox.confirm(`确定删除「${row.filename}」吗？`, '提示', { type: 'warning' })
  await api.delete(`/knowledge/${row.id}`)
  ElMessage.success('已删除')
  loadDocs()
}

const search = async () => {
  if (!query.value.trim()) return
  const res = await api.post('/knowledge/search', { query: query.value, top_k: 5 })
  searchResults.value = res.results
}

onMounted(loadDocs)
</script>

<style scoped>
.search-results {
  margin-top: 12px;
  max-height: 320px;
  overflow-y: auto;
}
.sr-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}
.sr-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.score {
  font-size: 12px;
  color: #909399;
}
.sr-item p {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}
</style>
