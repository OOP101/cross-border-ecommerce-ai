<template>
  <div class="page">
    <el-row :gutter="20" class="kpi-row">
      <el-col :span="6" v-for="k in kpis" :key="k.label">
        <el-card shadow="hover">
          <div class="kpi">
            <div class="kpi-label">{{ k.label }}</div>
            <div class="kpi-value">{{ k.value }}<span class="kpi-unit">{{ k.unit }}</span></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card header="意图分布">
          <div ref="intentChart" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="近 7 日对话趋势">
          <div ref="trendChart" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

const intentChart = ref(null)
const trendChart = ref(null)
const data = ref(null)

const kpis = computed(() => {
  const d = data.value?.kpi || {}
  return [
    { label: '累计对话数', value: d.total_conversations ?? 0, unit: '次' },
    { label: '平均响应延迟', value: d.avg_latency_ms ?? 0, unit: 'ms' },
    { label: '客服满意度', value: d.avg_rating ?? 0, unit: '分' },
    { label: 'Token 消耗', value: (d.total_prompt_tokens ?? 0) + (d.total_completion_tokens ?? 0), unit: '' },
  ]
})

const load = async () => {
  data.value = await api.get('/analytics/dashboard')
  renderCharts()
}

const renderCharts = () => {
  if (!data.value) return

  const intentData = data.value.intent_distribution || []
  if (intentChart.value) {
    echarts
      .init(intentChart.value)
      .setOption({
        tooltip: { trigger: 'item' },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            data: intentData.map((i) => ({ name: i.intent, value: i.count })),
          },
        ],
      })
  }

  const trend = data.value.conversation_trend || []
  if (trendChart.value) {
    echarts.init(trendChart.value).setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: trend.map((t) => t.date) },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'line',
          smooth: true,
          areaStyle: {},
          data: trend.map((t) => t.count),
        },
      ],
    })
  }
}

onMounted(load)
</script>

<style scoped>
.kpi-label {
  font-size: 13px;
  color: #909399;
}
.kpi-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-top: 8px;
}
.kpi-unit {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
  margin-left: 4px;
}
.chart {
  height: 300px;
}
</style>
