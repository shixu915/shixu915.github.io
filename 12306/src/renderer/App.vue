<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useNotification } from 'element-plus';

const notification = useNotification();

onMounted(() => {
  // 监听系统错误事件
  window.electronAPI.on.systemError((event, data) => {
    notification.error({
      title: '系统错误',
      message: data.message,
      duration: 0
    });
  });

  // 监听新通知事件
  window.electronAPI.on.notificationNew((event, data) => {
    notification({
      title: data.title,
      message: data.content,
      type: data.type,
      duration: 5000
    });
  });
});

onUnmounted(() => {
  // 清理事件监听
  window.electronAPI.off.systemError(() => {});
  window.electronAPI.off.notificationNew(() => {});
});
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
</style>
