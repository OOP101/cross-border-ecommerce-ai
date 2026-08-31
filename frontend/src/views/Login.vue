<template>
  <div class="login-page">
    <el-card class="login-card">
      <div class="login-head">
        <span class="logo-mark">贸</span>
        <h2>国际贸易智能平台</h2>
        <p class="sub">登录以继续使用</p>
      </div>
      <el-form :model="form" label-position="top" @keyup.enter="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="用户名" autofocus />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-button type="primary" class="submit" :loading="loading" @click="submit">
          登 录
        </el-button>
      </el-form>
      <p class="tip">演示模式无需登录；默认管理员 admin / admin123</p>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { TOKEN_KEY } from '../api'

const router = useRouter()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

const submit = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await api.post('/auth/login', { username: form.username, password: form.password })
    localStorage.setItem(TOKEN_KEY, res.access_token)
    ElMessage.success('登录成功')
    router.push('/chat')
  } catch (e) {
    // 错误提示由 axios 拦截器统一弹出
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #001529 0%, #0a2a4a 100%);
}
.login-card {
  width: 380px;
  padding: 12px 8px;
}
.login-head {
  text-align: center;
  margin-bottom: 12px;
}
.login-head h2 {
  margin: 10px 0 4px;
  color: #303133;
}
.login-head .sub {
  margin: 0 0 8px;
  color: #909399;
  font-size: 13px;
}
.logo-mark {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #409eff;
  color: #fff;
  font-size: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.submit {
  width: 100%;
  margin-top: 4px;
}
.tip {
  margin: 14px 0 0;
  text-align: center;
  color: #909399;
  font-size: 12px;
}
</style>
