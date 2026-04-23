<template>
  <div class="task-view">
    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建任务
      </el-button>
      <el-button @click="refreshTasks">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 任务列表 -->
    <el-table
      :data="tasks"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="任务名称" width="200" />
      <el-table-column label="出发地→目的地" width="200">
        <template #default="{ row }">
          {{ row.config.departure }} → {{ row.config.destination }}
        </template>
      </el-table-column>
      <el-table-column prop="config.date" label="出发日期" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="180" />
      <el-table-column label="操作" fixed="right" width="250">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending'"
            type="success"
            size="small"
            @click="startTask(row.id)"
          >
            启动
          </el-button>
          <el-button
            v-if="row.status === 'running'"
            type="warning"
            size="small"
            @click="pauseTask(row.id)"
          >
            暂停
          </el-button>
          <el-button
            v-if="row.status === 'paused'"
            type="success"
            size="small"
            @click="resumeTask(row.id)"
          >
            恢复
          </el-button>
          <el-button
            v-if="['pending', 'paused', 'failed'].includes(row.status)"
            type="danger"
            size="small"
            @click="cancelTask(row.id)"
          >
            取消
          </el-button>
          <el-button
            type="primary"
            size="small"
            @click="viewTaskDetail(row)"
          >
            详情
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="deleteTask(row.id)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 任务创建对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建抢票任务"
      width="600px"
    >
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="出发地" required>
          <el-input v-model="taskForm.departure" placeholder="请输入出发地" />
        </el-form-item>
        <el-form-item label="目的地" required>
          <el-input v-model="taskForm.destination" placeholder="请输入目的地" />
        </el-form-item>
        <el-form-item label="出发日期" required>
          <el-date-picker
            v-model="taskForm.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="座位类型" required>
          <el-checkbox-group v-model="taskForm.seatTypes">
            <el-checkbox label="二等座" />
            <el-checkbox label="一等座" />
            <el-checkbox label="商务座" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="启用候补">
          <el-switch v-model="taskForm.enableWaitlist" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createTask">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh } from '@element-plus/icons-vue';
import { ITask, TaskStatus } from '../../shared/types';

const tasks = ref<ITask[]>([]);
const loading = ref(false);
const createDialogVisible = ref(false);

const taskForm = ref({
  name: '',
  departure: '',
  destination: '',
  date: '',
  seatTypes: ['二等座'],
  enableWaitlist: true
});

onMounted(() => {
  refreshTasks();
});

async function refreshTasks() {
  loading.value = true;
  try {
    const result = await window.electronAPI.task.list();
    if (result.success) {
      tasks.value = result.data;
    }
  } catch (error) {
    ElMessage.error('获取任务列表失败');
  } finally {
    loading.value = false;
  }
}

function showCreateDialog() {
  createDialogVisible.value = true;
}

async function createTask() {
  try {
    const result = await window.electronAPI.task.create(taskForm.value);
    if (result.success) {
      ElMessage.success('任务创建成功');
      createDialogVisible.value = false;
      refreshTasks();
    }
  } catch (error) {
    ElMessage.error('任务创建失败');
  }
}

async function startTask(taskId: number) {
  try {
    const result = await window.electronAPI.task.start(taskId);
    if (result.success) {
      ElMessage.success('任务已启动');
      refreshTasks();
    }
  } catch (error) {
    ElMessage.error('启动任务失败');
  }
}

async function pauseTask(taskId: number) {
  try {
    const result = await window.electronAPI.task.pause(taskId);
    if (result.success) {
      ElMessage.success('任务已暂停');
      refreshTasks();
    }
  } catch (error) {
    ElMessage.error('暂停任务失败');
  }
}

async function resumeTask(taskId: number) {
  try {
    const result = await window.electronAPI.task.resume(taskId);
    if (result.success) {
      ElMessage.success('任务已恢复');
      refreshTasks();
    }
  } catch (error) {
    ElMessage.error('恢复任务失败');
  }
}

async function cancelTask(taskId: number) {
  try {
    await ElMessageBox.confirm('确定要取消该任务吗？', '提示', {
      type: 'warning'
    });
    const result = await window.electronAPI.task.cancel(taskId);
    if (result.success) {
      ElMessage.success('任务已取消');
      refreshTasks();
    }
  } catch (error) {
    // 用户取消操作
  }
}

async function deleteTask(taskId: number) {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？', '提示', {
      type: 'warning'
    });
    const result = await window.electronAPI.task.delete(taskId);
    if (result.success) {
      ElMessage.success('任务已删除');
      refreshTasks();
    }
  } catch (error) {
    // 用户取消操作
  }
}

function viewTaskDetail(task: ITask) {
  // TODO: 实现任务详情查看
  ElMessage.info('任务详情功能开发中');
}

function getStatusType(status: TaskStatus) {
  const typeMap: Record<TaskStatus, string> = {
    [TaskStatus.PENDING]: 'info',
    [TaskStatus.SCHEDULED]: 'info',
    [TaskStatus.RUNNING]: 'success',
    [TaskStatus.PAUSED]: 'warning',
    [TaskStatus.SUCCESS]: 'success',
    [TaskStatus.FAILED]: 'danger',
    [TaskStatus.CANCELLED]: 'info'
  };
  return typeMap[status] || 'info';
}

function getStatusText(status: TaskStatus) {
  const textMap: Record<TaskStatus, string> = {
    [TaskStatus.PENDING]: '待执行',
    [TaskStatus.SCHEDULED]: '已调度',
    [TaskStatus.RUNNING]: '运行中',
    [TaskStatus.PAUSED]: '已暂停',
    [TaskStatus.SUCCESS]: '成功',
    [TaskStatus.FAILED]: '失败',
    [TaskStatus.CANCELLED]: '已取消'
  };
  return textMap[status] || status;
}
</script>

<style scoped>
.task-view {
  height: 100%;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}
</style>
