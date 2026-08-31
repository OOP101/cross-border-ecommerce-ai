<template>
  <div class="page">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-head">
              <span>原文</span>
              <el-select v-model="form.source_language" size="small" style="width: 140px">
                <el-option v-for="l in langs" :key="l.code" :label="l.name" :value="l.code" />
              </el-select>
            </div>
          </template>
          <el-input
            v-model="form.text"
            type="textarea"
            :rows="12"
            placeholder="请输入待翻译的文本…"
          />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-head">
              <span>译文</span>
              <el-select v-model="form.target_language" size="small" style="width: 140px">
                <el-option v-for="l in langs" :key="l.code" :label="l.name" :value="l.code" />
              </el-select>
            </div>
          </template>
          <div class="translation-box">
            <el-icon v-if="!result" class="empty-icon"><Switch /></el-icon>
            <div v-if="!result" class="empty-text">译文将显示在这里</div>
            <div v-else class="result-text">{{ result.translation }}</div>
          </div>
          <div v-if="result" class="translation-meta">
            <el-tag size="small" :type="result.source === 'memory' ? 'success' : 'primary'" effect="plain">
              {{ result.source === 'memory' ? '翻译记忆命中' : '模型翻译' }}
            </el-tag>
            <el-button type="success" size="small" @click="copy">复制</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="actions">
      <el-checkbox v-model="form.use_terminology">使用术语库</el-checkbox>
      <el-checkbox v-model="form.use_memory">启用翻译记忆</el-checkbox>
      <el-button type="primary" :loading="loading" @click="translate">立即翻译</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const langs = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: '英语' },
  { code: 'fr', name: '法语' },
  { code: 'es', name: '西班牙语' },
  { code: 'ar', name: '阿拉伯语' },
  { code: 'ja', name: '日语' },
  { code: 'ko', name: '韩语' },
  { code: 'de', name: '德语' },
  { code: 'ru', name: '俄语' },
  { code: 'pt', name: '葡萄牙语' },
  { code: 'it', name: '意大利语' },
]

const form = ref({
  text: '',
  source_language: 'zh',
  target_language: 'en',
  use_terminology: true,
  use_memory: true,
})
const loading = ref(false)
const result = ref(null)

const translate = async () => {
  if (!form.value.text.trim()) {
    ElMessage.warning('请输入待翻译文本')
    return
  }
  loading.value = true
  try {
    result.value = await api.post('/translation/translate', form.value)
  } finally {
    loading.value = false
  }
}

const copy = async () => {
  try {
    await navigator.clipboard.writeText(result.value.translation)
    ElMessage.success('已复制')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.translation-box {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.empty-icon {
  font-size: 40px;
  color: #dcdfe6;
}
.empty-text {
  margin-top: 8px;
  color: #c0c4cc;
  font-size: 14px;
}
.result-text {
  width: 100%;
  font-size: 15px;
  line-height: 1.7;
  color: #303133;
  white-space: pre-wrap;
}
.translation-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}
.actions {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>
