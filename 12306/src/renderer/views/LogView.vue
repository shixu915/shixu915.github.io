<template>
  <div class="log-view">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="logLevel" placeholder="日志级别" style="width: 120px">
        <el-option label="全部" value="" />
        <el-option label="错误" value="error" />
        <el-option label="警告" value="warn" />
        <el-option label="信息" value="info" />
        <el-option label="调试" value="debug" />
      </el-select>
      
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 300px; margin-left: 10px"
      />
      
      <el-input
        v-model="searchKeyword"
        placeholder="搜索关键词"
        style="width: 200px; margin-left: 10px"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-button type="primary" style="margin-left: 10px" @click="queryLogs">
        查询
      </el-button>
      
      <el-button @click="exportLogs">
        <el-icon><Download /></el-icon>
        导出
      </el-button>
    </div>

    <!-- 日志列表 -->
    <div class="log-list" ref="logListRef">
      <div
        v-for="log in logs"
        :key="log.id"
        class="log-item"
        :class="`log-${log.level}`"
      >
        <span class="log-time">{{ log.createdAt }}</span>
        <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
        <span class="log-message">{{ log.message }}</span>
        <span v-if="log.source" class="log-source">({{ log.source }})</span>
      </div>
      
      <el-empty v-if="logs.length === 0" description="暂无日志" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Search, Download } from '@element-plus/icons-vue';
import { ILog } from '../../shared/types';

const logs = ref<ILog[]>([]);
const logLevel = ref('');
const dateRange = ref([]);
const searchKeyword = ref('');
const logListRef = ref<HTMLElement>();

onMounted(() => {
  queryLogs();
  
  // 监听新日志事件
  window.electronAPI.on.logNew((event, log) => {
    logs.value.unshift(log);
    // 保持最新100条日志
    if (logs.value.length > 100) {
      logs.value.pop();
    }
  });
});

async function queryLogs() {
  try {
    const result = await window.electronAPI.log.query({
      level: logLevel.value,
      dateRange: dateRange.value,
      keyword: searchKeyword.value
    });
    if (result.success) {
      logs.value = result.data;
    }
  } catch (error) {
    ElMessage.error('查询日志失败');
  }
}

function exportLogs() {
  // TODO: 实现日志导出功能
  ElMessage.info('日志导出功能开发中');
}
</script>

<style scoped>
.log-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
}

.log-item {
  padding: 8px 0;
  border-bottom: 1px solid #f2f2f2;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #909399;
  margin-right: 10px;
}

.log-level {
  font-weight: bold;
  margin-right: 10px;
}

.log-message {
  color: #303133;
}

.log-source {
  color: #909399;
  margin-left: 10px;
}

.log-error .log-level {
  color: #f56c6c;
}

.log-warn .log-level {
  color: #e6a23c;
}

.log-info .log-level {
  color: #409eff;
}

.log-debug .log-level {
  color: #909399;
}
</style>
