<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span class="logo-mark">贸</span>
        <span class="logo-text">国际贸易智能平台</span>
      </div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ currentTitle }}</div>
        <div class="header-right">
          <el-tag size="small" type="success" effect="plain">v0.2 待孵化</el-tag>
          <el-dropdown v-if="me" @command="onCommand">
            <span class="user-chip">
              <el-icon><User /></el-icon>
              {{ me.sub }}（{{ roleLabel(me.role) }}）
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ME_KEY, clearAuth } from '../api'

const route = useRoute()
const router = useRouter()

const menus = [
  { path: '/chat', title: '智能客服', icon: 'ChatDotRound' },
  { path: '/copywriting', title: '智能文案', icon: 'EditPen' },
  { path: '/translation', title: '翻译引擎', icon: 'Switch' },
  { path: '/knowledge', title: '知识库管理', icon: 'Collection' },
  { path: '/analytics', title: '数据洞察', icon: 'DataAnalysis' },
  { path: '/admin', title: '管理后台', icon: 'Setting' },
]

const roleMap = { admin: '管理员', operator: '运营', viewer: '访客' }
const roleLabel = (r) => roleMap[r] || r

const me = ref(null)
try {
  me.value = JSON.parse(localStorage.getItem(ME_KEY) || 'null')
} catch {
  me.value = null
}

const onCommand = (cmd) => {
  if (cmd === 'logout') {
    clearAuth()
    router.push('/login')
  }
}

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #001529;
  color: #fff;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  color: #fff;
  font-weight: 600;
}
.logo-mark {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
.logo-text {
  font-size: 14px;
}
.menu {
  border-right: none;
  background: transparent;
}
.menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.75);
}
.menu :deep(.el-menu-item.is-active) {
  background: #409eff;
  color: #fff;
}
.menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
}
.header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #606266;
  font-size: 13px;
  outline: none;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.main {
  padding: 20px;
  overflow-y: auto;
  background: #f5f7fa;
}
</style>
