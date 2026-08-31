<template>
  <div class="page">
    <!-- 一、文案模板卡片（点击选择类型） -->
    <div class="section-title">① 选择文案模板</div>
    <div class="template-grid">
      <div
        v-for="t in templates"
        :key="t.type"
        class="template-card"
        :class="{ active: form.copy_type === t.type }"
        @click="form.copy_type = t.type"
      >
        <div class="t-icon">{{ t.icon }}</div>
        <div class="t-name">{{ t.name }}</div>
        <div class="t-desc">{{ t.desc }}</div>
        <div class="t-outputs">
          <el-tag v-for="o in t.outputs" :key="o" size="small" effect="plain">{{ o }}</el-tag>
        </div>
      </div>
    </div>

    <!-- 二、示例商品一键填充 -->
    <div class="section-title">② 一键填充示例商品（或手动填写）</div>
    <div class="preset-grid">
      <div
        v-for="p in presets"
        :key="p.name"
        class="preset-card"
        @click="applyPreset(p)"
      >
        <div class="p-icon">{{ p.icon }}</div>
        <div class="p-name">{{ p.name }}</div>
        <div class="p-desc">{{ p.selling_points }}</div>
      </div>
    </div>

    <!-- 三、参数与生成 -->
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card header="商品信息">
          <el-form :model="form" label-width="90px" label-position="left" size="large">
            <el-form-item label="商品名称">
              <el-input v-model="form.product_name" placeholder="如：智能 LED 灯带" />
            </el-form-item>
            <el-form-item label="品类">
              <el-input v-model="form.category" placeholder="如：智能家居" />
            </el-form-item>
            <el-form-item label="卖点关键词">
              <el-input v-model="form.selling_points" type="textarea" :rows="2" placeholder="RGB变色、App控制、节能环保" />
            </el-form-item>
            <el-form-item label="目标市场">
              <el-input v-model="form.target_market" placeholder="如：欧美 / 东南亚 / 中东" />
            </el-form-item>
            <el-form-item label="目标语言">
              <el-select v-model="form.target_language" style="width: 100%">
                <el-option v-for="l in langs" :key="l.code" :label="l.name" :value="l.code" />
              </el-select>
            </el-form-item>
            <el-form-item label="风格 / 语气">
              <div class="style-row">
                <el-select v-model="form.style" placeholder="风格" allow-create filterable style="width: 100%">
                  <el-option v-for="s in styleOptions" :key="s" :label="s" :value="s" />
                </el-select>
                <el-select v-model="form.tone" placeholder="语气" allow-create filterable style="width: 100%">
                  <el-option v-for="t in toneOptions" :key="t" :label="t" :value="t" />
                </el-select>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" class="gen-btn" :loading="loading" @click="generate">
                ⚡ 一键生成{{ currentTemplate?.name || '文案' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="result-head">
              <span>生成结果</span>
              <el-button v-if="result" type="success" size="small" @click="copyResult">复制全部</el-button>
            </div>
          </template>
          <el-empty v-if="!result && !loading" description="选择模板 → 填写商品 → 一键生成" />
          <div v-if="loading" class="gen-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>AI 正在创作中，多段文案并发生成…</span>
          </div>
          <div v-if="result" class="result">
            <div v-for="block in resultBlocks" :key="block.key" class="block">
              <div class="block-head">
                <div class="label">{{ block.label }}</div>
                <el-button text size="small" type="primary" @click="copyOne(block.text)">复制</el-button>
              </div>
              <div class="text" :class="{ pre: block.pre }">{{ block.text }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const templates = [
  { type: 'all', icon: '🚀', name: '一键全套', desc: '上架所需一次生成', outputs: ['标题', '详情', '广告语', '关键词'] },
  { type: 'product', icon: '📝', name: '商品详情', desc: '商品上架完整信息', outputs: ['标题', '详情', '关键词'] },
  { type: 'ad', icon: '📢', name: '投放广告语', desc: 'Google / Facebook 投放', outputs: ['广告语'] },
  { type: 'campaign', icon: '🎉', name: '活动文案', desc: '促销 / 节日营销主题', outputs: ['活动文案'] },
  { type: 'keywords', icon: '🔍', name: 'SEO 关键词', desc: '搜索引擎优化标签', outputs: ['关键词'] },
]

// 示例商品模板（与示例知识库一致），点击一键填充
const presets = [
  {
    icon: '💡', name: '智能 LED 灯带', category: '智能家居',
    selling_points: 'RGB变色、App与语音控制、节能环保',
    target_market: '欧美、东南亚',
  },
  {
    icon: '☀️', name: '便携太阳能充电板', category: '户外装备',
    selling_points: '21W折叠、双USB输出、IPX4防水',
    target_market: '欧美、中东',
  },
  {
    icon: '🎧', name: '无线蓝牙耳机', category: '消费电子',
    selling_points: '蓝牙5.3、30小时续航、主动降噪',
    target_market: '全球',
  },
]

const langs = [
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
  { code: 'zh', name: '中文' },
]

const styleOptions = ['专业', '活泼', '高端', '科技感', '简约']
const toneOptions = ['亲切', '正式', '热情', '克制']

const form = ref({
  copy_type: 'all',
  product_name: '',
  category: '',
  selling_points: '',
  target_market: '',
  target_language: 'en',
  style: '',
  tone: '',
})
const loading = ref(false)
const result = ref(null)

const currentTemplate = computed(() => templates.find((t) => t.type === form.value.copy_type))

const applyPreset = (p) => {
  form.value.product_name = p.name
  form.value.category = p.category
  form.value.selling_points = p.selling_points
  form.value.target_market = p.target_market
  ElMessage.success(`已填充「${p.name}」，可直接生成`)
}

const generate = async () => {
  if (!form.value.product_name) {
    ElMessage.warning('请填写商品名称，或点击上方示例商品一键填充')
    return
  }
  loading.value = true
  result.value = null
  try {
    result.value = await api.post('/copywriting/generate', form.value)
  } finally {
    loading.value = false
  }
}

const labelMap = { title: '商品标题', description: '商品描述', ad: '广告语', campaign: '活动文案', keywords: 'SEO 关键词' }

const resultBlocks = computed(() => {
  if (!result.value) return []
  return Object.entries(result.value)
    .filter(([k]) => labelMap[k])
    .map(([k, v]) => ({ key: k, label: labelMap[k], text: v, pre: k !== 'title' && k !== 'keywords' }))
})

const copyOne = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

const resultText = computed(() =>
  resultBlocks.value.map((b) => `【${b.label}】\n${b.text}`).join('\n\n')
)

const copyResult = async () => {
  try {
    await navigator.clipboard.writeText(resultText.value)
    ElMessage.success('已复制全部')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 4px 0 12px;
}

/* ---- 模板卡片 ---- */
.template-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 22px;
}
.template-card {
  padding: 14px;
  border: 2px solid #ebeef5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}
.template-card:hover {
  border-color: #a0cfff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.12);
}
.template-card.active {
  border-color: #409eff;
  background: linear-gradient(180deg, #ecf5ff 0%, #ffffff 100%);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.18);
}
.t-icon {
  font-size: 26px;
}
.t-name {
  margin-top: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #303133;
}
.t-desc {
  margin: 4px 0 8px;
  font-size: 12px;
  color: #909399;
}
.t-outputs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* ---- 示例商品卡片 ---- */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 22px;
}
.preset-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px dashed #dcdfe6;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbfc;
}
.preset-card:hover {
  border-color: #67c23a;
  background: #f0f9eb;
  transform: translateY(-2px);
}
.p-icon {
  font-size: 24px;
}
.p-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.p-desc {
  margin-top: 2px;
  font-size: 12px;
  color: #909399;
}

.style-row {
  display: flex;
  gap: 8px;
}
.gen-btn {
  width: 100%;
}
.result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.gen-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 0;
  color: #909399;
  font-size: 14px;
}

/* ---- 结果分块 ---- */
.result .block {
  margin-bottom: 16px;
}
.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.result .label {
  font-size: 13px;
  color: #909399;
}
.result .text {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
}
.result .text.pre {
  white-space: pre-wrap;
  background: #f8f9fb;
  padding: 10px;
  border-radius: 8px;
}
</style>
