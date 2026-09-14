<template>
  <div class="kb-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover"><div class="stat-num">{{ stats.documents }}</div><div class="stat-label">文档总数</div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover"><div class="stat-num">{{ stats.chunks }}</div><div class="stat-label">知识片段总数</div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover"><div class="stat-num success">{{ stats.by_status?.indexed?.documents || 0 }}</div><div class="stat-label">已索引文档</div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover"><div class="stat-num warning">{{ busyCount }}</div><div class="stat-label">处理中 / 失败</div></el-card>
      </el-col>
    </el-row>

    <!-- 上传区 -->
    <el-card class="upload-card">
      <div class="upload-row">
        <el-input
          v-model="category"
          placeholder="商品类目,如: 手机数码"
          style="width: 240px"
          clearable
        />
        <el-upload
          :show-file-list="false"
          :http-request="doUpload"
          :before-upload="beforeUpload"
          accept=".md,.markdown,.txt,.pdf,.docx,.xlsx"
        >
          <el-button type="primary">选择文件上传</el-button>
        </el-upload>
        <span class="tip">支持 md / markdown / txt / pdf / docx / xlsx,上限 20MB,上传后自动解析入库</span>
      </div>
    </el-card>

    <!-- 文档列表 -->
    <el-card>
      <template #header><span>知识库文档</span></template>
      <el-table :data="documents" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="类目" width="110" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'indexed'" type="success">已索引</el-tag>
            <el-tag v-else-if="row.status === 'parsing'" type="warning">解析中</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else type="info">待处理</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="片段数" width="90" />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="失败原因" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span :class="{ err: row.status === 'failed' }">{{ row.error_msg || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="上传时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="reprocess(row)">重新解析</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteDocument, kbStats, listDocuments, reprocessDocument, uploadDocument } from '../../api/kb'
import { extractErrMsg } from '../../api/request'

const documents = ref([])
const stats = ref({ documents: 0, chunks: 0, by_status: {} })
const category = ref('通用')
const loading = ref(false)
let pollTimer = null

const busyCount = computed(
  () =>
    (stats.value.by_status?.parsing?.documents || 0) +
    (stats.value.by_status?.failed?.documents || 0),
)

async function refresh() {
  try {
    const [docs, st] = await Promise.all([listDocuments(), kbStats()])
    documents.value = docs
    stats.value = st
    // 有文档在解析中时自动轮询,完成后停止
    const busy = docs.some((d) => d.status === 'pending' || d.status === 'parsing')
    if (busy && !pollTimer) {
      pollTimer = setInterval(refresh, 3000)
    } else if (!busy && pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  } catch (e) {
    ElMessage.error(extractErrMsg(e))
  } finally {
    loading.value = false
  }
}

function beforeUpload(file) {
  const ext = (file.name || '').split('.').pop().toLowerCase()
  const ok = ['md', 'markdown', 'txt', 'pdf', 'docx', 'xlsx'].includes(ext)
  if (!ok) ElMessage.error(`不支持的文件类型: ${ext}`)
  return ok
}

async function doUpload({ file }) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('category', category.value || '通用')
  loading.value = true
  try {
    await uploadDocument(fd)
    ElMessage.success(`《${file.name}》上传成功,后台解析中`)
    await refresh()
  } catch (e) {
    ElMessage.error(extractErrMsg(e))
  } finally {
    loading.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除《${row.name}》?其全部知识片段将从向量库移除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return // 用户取消
  }
  try {
    await deleteDocument(row.id)
    ElMessage.success('删除成功')
    await refresh()
  } catch (e) {
    ElMessage.error(extractErrMsg(e))
  }
}

async function reprocess(row) {
  try {
    await reprocessDocument(row.id)
    ElMessage.success('已提交重新解析')
    await refresh()
  } catch (e) {
    ElMessage.error(extractErrMsg(e))
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function formatTime(s) {
  return s ? s.replace('T', ' ').slice(0, 19) : '-'
}

onMounted(refresh)
onUnmounted(() => pollTimer && clearInterval(pollTimer))
</script>

<style scoped>
.stat-row {
  margin-bottom: 16px;
}
.stat-num {
  font-size: 26px;
  font-weight: 700;
}
.stat-num.success {
  color: #67c23a;
}
.stat-num.warning {
  color: #e6a23c;
}
.stat-label {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}
.upload-card {
  margin-bottom: 16px;
}
.upload-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.tip {
  color: #909399;
  font-size: 13px;
}
.err {
  color: #f56c6c;
}
</style>
