<template>
  <div class="page">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card header="系统运行状态">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="应用名称">{{ status.app }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ status.version }}</el-descriptions-item>
            <el-descriptions-item label="LLM 提供商">{{ status.llm_provider }}（{{ status.llm_impl }}）</el-descriptions-item>
            <el-descriptions-item label="LLM 模型">{{ status.llm_model }}</el-descriptions-item>
            <el-descriptions-item label="嵌入提供商">{{ status.embedding_provider }}</el-descriptions-item>
            <el-descriptions-item label="向量库">{{ status.vector_store }}</el-descriptions-item>
            <el-descriptions-item label="向量条目数">{{ status.vector_count }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card header="知识库统计" style="margin-top: 20px">
          <el-statistic title="文档数" :value="knowledgeStats.documents ?? 0" />
          <el-statistic title="向量分块数" :value="knowledgeStats.chunks ?? 0" style="margin-left: 60px" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card header="审计日志">
          <el-table :data="logs" height="440" stripe size="small">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="actor" label="操作者" width="90" />
            <el-table-column prop="action" label="动作" width="120" />
            <el-table-column prop="detail" label="详情" min-width="140" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const status = ref({})
const knowledgeStats = ref({})
const logs = ref([])

const load = async () => {
  const [s, k, a] = await Promise.all([
    api.get('/admin/status'),
    api.get('/admin/knowledge-stats'),
    api.get('/admin/audit'),
  ])
  status.value = s
  knowledgeStats.value = k
  logs.value = a.logs
}

onMounted(load)
</script>
