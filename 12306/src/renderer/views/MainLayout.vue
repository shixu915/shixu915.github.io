<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <el-icon :size="32"><Ticket /></el-icon>
        <span>小鲁班抢票助手</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
        
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <span>系统日志</span>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶栏 -->
      <el-header class="header">
        <div class="header-left">
          <h2>{{ currentTitle }}</h2>
        </div>
        <div class="header-right">
          <el-badge :value="notificationCount" :hidden="notificationCount === 0">
            <el-button circle>
              <el-icon><Bell /></el-icon>
            </el-button>
          </el-badge>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { Ticket, List, Document, Setting, Bell } from '@element-plus/icons-vue';

const route = useRoute();
const notificationCount = ref(0);

const activeMenu = computed(() => route.path);
const currentTitle = computed(() => route.meta.title as string || '小鲁班抢票助手');
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background-color: #545c64;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #434a50;
}

.sidebar-menu {
  border: none;
  background-color: #545c64;
}

.sidebar-menu .el-menu-item {
  color: #fff;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #434a50;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #409eff;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
