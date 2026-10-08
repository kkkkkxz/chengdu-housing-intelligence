<template>
  <div class="house-manage">
    <div class="toolbar">
      <n-button type="primary" @click="openCreateModal">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        新增房源
      </n-button>
    </div>

    <n-data-table
      :columns="columns"
      :data="houseList"
      :loading="loading"
      :pagination="pagination"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      remote
    />

    <!-- 新增/编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 800px">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="120px">
        <n-grid :cols="2" :x-gap="16">
          <n-grid-item>
            <n-form-item label="标题" path="title">
              <n-input v-model:value="formData.title" placeholder="请输入标题" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="城市" path="city">
              <n-input v-model:value="formData.city" placeholder="如：成都市" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="区域" path="district">
              <n-input v-model:value="formData.district" placeholder="如：锦江" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="小区" path="community">
              <n-input v-model:value="formData.community" placeholder="小区名称" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="详细地址" path="address">
              <n-input v-model:value="formData.address" placeholder="详细地址" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="总价(万元)" path="total_price">
              <n-input-number v-model:value="formData.total_price" :min="0" :step="1" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="单价(元/㎡)" path="unit_price">
              <n-input-number v-model:value="formData.unit_price" :min="0" :step="100" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="面积(㎡)" path="area">
              <n-input-number v-model:value="formData.area" :min="0" :step="1" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="室" path="rooms">
              <n-input-number v-model:value="formData.rooms" :min="0" :max="10" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="厅" path="halls">
              <n-input-number v-model:value="formData.halls" :min="0" :max="10" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="朝向" path="orientation">
              <n-input v-model:value="formData.orientation" placeholder="如：北南" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="楼层" path="floor">
              <n-input v-model:value="formData.floor" placeholder="如：高楼层(共34层)" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="装修" path="decorate">
              <n-select v-model:value="formData.decorate" :options="decorateOptions" placeholder="请选择装修" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="建筑类型" path="building_type">
              <n-select v-model:value="formData.building_type" :options="buildingTypeOptions" placeholder="请选择" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="关注人数" path="followers">
              <n-input-number v-model:value="formData.followers" :min="0" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="房源链接" path="link">
              <n-input v-model:value="formData.link" placeholder="链家链接" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="2">
            <n-form-item label="封面图URL" path="cover">
              <n-input v-model:value="formData.cover" placeholder="图片URL" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="2">
            <n-form-item label="标签" path="tags">
              <n-input v-model:value="formData.tags" placeholder="多个标签用/分隔" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="经度" path="longitude">
              <n-input-number v-model:value="formData.longitude" :precision="6" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="纬度" path="latitude">
              <n-input-number v-model:value="formData.latitude" :precision="6" style="width: 100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="2">
            <n-form-item label="本地图片路径" path="local_image_path">
              <n-input v-model:value="formData.local_image_path" placeholder="本地图片路径（可选）" />
            </n-form-item>
          </n-grid-item>
        </n-grid>
      </n-form>
      <template #footer>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" @click="submitForm" :loading="submitting">提交</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import type { VNode } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMessage, useDialog, NButton, NIcon, NDataTable, NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NGrid, NGridItem } from 'naive-ui'
import type { FormRules } from 'naive-ui'
import { AddOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5'
import axios from 'axios'
// 导入带 token 拦截器的 request 实例（根据实际路径调整）
import request from '@/api/request'

const authStore = useAuthStore()
const message = useMessage()
const dialog = useDialog()

const houseList = ref<any[]>([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0
})

const showModal = ref(false)
const modalTitle = ref('新增房源')
const formRef = ref()
const submitting = ref(false)
const editId = ref<number | null>(null)

// 表单数据，rooms/halls/followers 默认值为 0
const formData = ref({
  title: '',
  city: '',
  district: '',
  community: '',
  address: '',
  total_price: null as number | null,
  unit_price: null as number | null,
  area: null as number | null,
  rooms: 0,
  halls: 0,
  orientation: '',
  floor: '',
  decorate: '',
  building_type: '',
  followers: 0,
  link: '',
  cover: '',
  tags: '',
  longitude: null as number | null,
  latitude: null as number | null,
  local_image_path: ''
})

const decorateOptions = [
  { label: '精装', value: '精装' },
  { label: '简装', value: '简装' },
  { label: '毛坯', value: '毛坯' },
  { label: '其他', value: '其他' }
]

const buildingTypeOptions = [
  { label: '板楼', value: '板楼' },
  { label: '塔楼', value: '塔楼' },
  { label: '板塔结合', value: '板塔结合' },
  { label: '其他', value: '其他' }
]

const rules: FormRules = {
  title: { required: true, message: '请输入标题', trigger: 'blur' },
  city: { required: true, message: '请输入城市', trigger: 'blur' },
  total_price: { required: true, type: 'number', message: '请输入总价', trigger: 'blur' },
  area: { required: true, type: 'number', message: '请输入面积', trigger: 'blur' }
}

const columns = computed(() => {
  const baseColumns: any[] = [
    { title: 'ID', key: 'id', width: 60 },
    { title: '标题', key: 'title', ellipsis: { tooltip: true } },
    { title: '城市', key: 'city', width: 100 },
    { title: '区域', key: 'district', width: 100 },
    { title: '小区', key: 'community', width: 150, ellipsis: { tooltip: true } },
    { title: '总价(万)', key: 'total_price', width: 100 },
    { title: '面积(㎡)', key: 'area', width: 90 },
    { title: '户型', key: 'rooms', width: 80, render: (row: any) => `${row.rooms}室${row.halls}厅` },
    { title: '装修', key: 'decorate', width: 80 }
  ]
  baseColumns.push({
    title: '操作',
    key: 'actions',
    width: 120,
    fixed: 'right',
    render(row: any): VNode {
      return h('div', { style: 'display: flex; gap: 8px;' }, [
        h(NButton, { size: 'small', type: 'primary', tertiary: true, onClick: () => openEditModal(row) },
          () => [h(NIcon, null, () => h(CreateOutline)), ' 编辑']),
        h(NButton, { size: 'small', type: 'error', tertiary: true, onClick: () => handleDelete(row) },
          () => [h(NIcon, null, () => h(TrashOutline)), ' 删除'])
      ])
    }
  })
  return baseColumns
})

const fetchHouses = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/listings/houses/', {
      params: {
        page: pagination.value.page,
        page_size: pagination.value.pageSize
      }
    })
    houseList.value = res.data.results || res.data
    pagination.value.itemCount = res.data.count || 0
  } catch (err) {
    message.error('获取房源列表失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchHouses()
}
const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  fetchHouses()
}

const openCreateModal = () => {
  editId.value = null
  modalTitle.value = '新增房源'
  formData.value = {
    title: '',
    city: '',
    district: '',
    community: '',
    address: '',
    total_price: null,
    unit_price: null,
    area: null,
    rooms: 0,
    halls: 0,
    orientation: '',
    floor: '',
    decorate: '',
    building_type: '',
    followers: 0,
    link: '',
    cover: '',
    tags: '',
    longitude: null,
    latitude: null,
    local_image_path: ''
  }
  showModal.value = true
}

const openEditModal = (row: any) => {
  editId.value = row.id
  modalTitle.value = '编辑房源'
  formData.value = { 
    ...row,
    rooms: row.rooms ?? 0,
    halls: row.halls ?? 0,
    followers: row.followers ?? 0
  }
  showModal.value = true
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    if (editId.value) {
      await request.put(`/listings/houses/${editId.value}/`, formData.value)
      message.success('修改成功')
    } else {
      await request.post('/listings/houses/', formData.value)
      message.success('新增成功')
    }
    showModal.value = false
    fetchHouses()
  } catch (err: any) {
    console.error('提交失败:', err.response?.data || err.message)
    message.error(err.response?.data?.detail || err.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row: any) => {
  dialog.warning({
    title: '确认删除',
    content: `确定删除房源“${row.title}”吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.delete(`/listings/houses/${row.id}/`)
        message.success('删除成功')
        fetchHouses()
      } catch (err) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  fetchHouses()
})
</script>

<style scoped>
.house-manage {
  padding: 16px;
}
.toolbar {
  margin-bottom: 16px;
}
</style>