<template>
  <div class="settings-view">
    <el-card>
      <template #header>
        <span>通知设置</span>
      </template>
      <el-form label-width="150px">
        <el-form-item label="启用通知">
          <el-switch v-model="settings.notificationEnabled" />
        </el-form-item>
        <el-form-item label="通知渠道">
          <el-checkbox-group v-model="settings.notificationChannels">
            <el-checkbox label="desktop">桌面通知</el-checkbox>
            <el-checkbox label="email">邮件通知</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="邮件服务器">
          <el-input v-model="settings.emailHost" placeholder="smtp.example.com" />
        </el-form-item>
        <el-form-item label="邮件端口">
          <el-input v-model="settings.emailPort" placeholder="587" />
        </el-form-item>
        <el-form-item label="邮件用户名">
          <el-input v-model="settings.emailUser" placeholder="your@email.com" />
        </el-form-item>
        <el-form-item label="邮件密码">
          <el-input v-model="settings.emailPassword" type="password" show-password />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>抢票设置</span>
      </template>
      <el-form label-width="150px">
        <el-form-item label="重试次数">
          <el-input-number v-model="settings.retryTimes" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="最小延迟(毫秒)">
          <el-input-number v-model="settings.retryDelayMin" :min="500" :max="5000" :step="100" />
        </el-form-item>
        <el-form-item label="最大延迟(毫秒)">
          <el-input-number v-model="settings.retryDelayMax" :min="1000" :max="10000" :step="100" />
        </el-form-item>
        <el-form-item label="启用候补">
          <el-switch v-model="settings.enableWaitlist" />
        </el-form-item>
        <el-form-item label="查询间隔(毫秒)">
          <el-input-number v-model="settings.queryInterval" :min="100" :max="2000" :step="100" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>验证码设置</span>
      </template>
      <el-form label-width="150px">
        <el-form-item label="启用OCR识别">
          <el-switch v-model="settings.enableOcr" />
        </el-form-item>
        <el-form-item label="超时时间(秒)">
          <el-input-number v-model="settings.captchaTimeout" :min="30" :max="300" :step="10" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>系统设置</span>
      </template>
      <el-form label-width="150px">
        <el-form-item label="最大并发任务数">
          <el-input-number v-model="settings.maxConcurrentTasks" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="日志级别">
          <el-select v-model="settings.logLevel" style="width: 200px">
            <el-option label="错误" value="error" />
            <el-option label="警告" value="warn" />
            <el-option label="信息" value="info" />
            <el-option label="调试" value="debug" />
          </el-select>
        </el-form-item>
        <el-form-item label="日志保留天数">
          <el-input-number v-model="settings.logRetentionDays" :min="7" :max="90" :step="7" />
        </el-form-item>
      </el-form>
    </el-card>

    <div style="margin-top: 20px; text-align: right">
      <el-button @click="resetSettings">重置默认</el-button>
      <el-button type="primary" @click="saveSettings">保存设置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';

const settings = ref({
  notificationEnabled: true,
  notificationChannels: ['desktop'],
  emailHost: '',
  emailPort: '587',
  emailUser: '',
  emailPassword: '',
  retryTimes: 3,
  retryDelayMin: 1000,
  retryDelayMax: 3000,
  enableWaitlist: true,
  queryInterval: 500,
  enableOcr: false,
  captchaTimeout: 120,
  maxConcurrentTasks: 5,
  logLevel: 'info',
  logRetentionDays: 30
});

onMounted(() => {
  loadSettings();
});

async function loadSettings() {
  try {
    const result = await window.electronAPI.config.getAll();
    if (result.success) {
      // 将配置映射到settings
      Object.keys(result.data).forEach(key => {
        const value = result.data[key];
        // 简单的配置映射逻辑
        if (key === 'notification.enabled') {
          settings.value.notificationEnabled = value === 'true';
        }
        // 其他配置项映射...
      });
    }
  } catch (error) {
    ElMessage.error('加载配置失败');
  }
}

async function saveSettings() {
  try {
    // 保存各项配置
    await window.electronAPI.config.set('notification.enabled', settings.value.notificationEnabled.toString());
    await window.electronAPI.config.set('notification.channels', JSON.stringify(settings.value.notificationChannels));
    await window.electronAPI.config.set('notification.email.host', settings.value.emailHost);
    await window.electronAPI.config.set('notification.email.port', settings.value.emailPort);
    await window.electronAPI.config.set('notification.email.user', settings.value.emailUser);
    await window.electronAPI.config.set('notification.email.password', settings.value.emailPassword);
    await window.electronAPI.config.set('ticket.retry_times', settings.value.retryTimes.toString());
    await window.electronAPI.config.set('ticket.retry_delay_min', settings.value.retryDelayMin.toString());
    await window.electronAPI.config.set('ticket.retry_delay_max', settings.value.retryDelayMax.toString());
    await window.electronAPI.config.set('ticket.enable_waitlist', settings.value.enableWaitlist.toString());
    await window.electronAPI.config.set('ticket.query_interval', settings.value.queryInterval.toString());
    await window.electronAPI.config.set('captcha.enable_ocr', settings.value.enableOcr.toString());
    await window.electronAPI.config.set('captcha.timeout', settings.value.captchaTimeout.toString());
    await window.electronAPI.config.set('system.max_concurrent_tasks', settings.value.maxConcurrentTasks.toString());
    await window.electronAPI.config.set('system.log_level', settings.value.logLevel);
    await window.electronAPI.config.set('system.log_retention_days', settings.value.logRetentionDays.toString());
    
    ElMessage.success('设置保存成功');
  } catch (error) {
    ElMessage.error('保存设置失败');
  }
}

function resetSettings() {
  // 重置为默认值
  settings.value = {
    notificationEnabled: true,
    notificationChannels: ['desktop'],
    emailHost: '',
    emailPort: '587',
    emailUser: '',
    emailPassword: '',
    retryTimes: 3,
    retryDelayMin: 1000,
    retryDelayMax: 3000,
    enableWaitlist: true,
    queryInterval: 500,
    enableOcr: false,
    captchaTimeout: 120,
    maxConcurrentTasks: 5,
    logLevel: 'info',
    logRetentionDays: 30
  };
  ElMessage.success('已重置为默认设置');
}
</script>

<style scoped>
.settings-view {
  max-width: 800px;
}
</style>
