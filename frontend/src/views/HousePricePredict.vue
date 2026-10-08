<template>
  <div class="predict-page">
    <h2 class="title">房价预测</h2>

    <n-card>
      <n-space vertical size="large" style="width:100%">
        <n-row>
          <n-col :span="10">
            <n-form-item label="区县">
              <n-select
                v-model:value="form.district"
                :options="districts"
                placeholder="请选择区县"
                clearable
                style="width:100%"
              />
            </n-form-item>
          </n-col>
          <n-col :span="6">
            <n-form-item label="面积(m²)">
              <n-input-number v-model:value="form.area" :min="1" style="width:100%" />
            </n-form-item>
          </n-col>
          <n-col :span="4">
            <n-form-item label="室">
              <n-select v-model:value="form.rooms" :options="roomOptions" style="width:100%" />
            </n-form-item>
          </n-col>
          <n-col :span="4" class="tags-col">
            <n-space>
              <n-checkbox v-model:checked="form.has_vr">有VR</n-checkbox>
              <n-checkbox v-model:checked="form.has_metro">临近地铁</n-checkbox>
            </n-space>
          </n-col>
        </n-row>

        <div class="actions">
          <n-button type="primary" @click="onPredict" :loading="loading">预测</n-button>
          <n-button @click="reset">重置</n-button>
        </div>

        <div v-if="error" class="error">{{ error }}</div>

        <div v-if="result" class="result">
          <h3>预测结果</h3>
          <div>预测单价：<strong>{{ result.unit_price }}</strong> 元/㎡</div>
          <div>预测总价：<strong>{{ result.total_price }}</strong> 万</div>
        </div>

        <div v-if="!districts.length && !loading" class="hint">没有可用区县数据，模型未构建或数据为空。</div>
      </n-space>
    </n-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { getDistricts, predictPrice } from '@/api/prediction'

const districts = ref<Array<{ label: string; value: string }>>([])
const roomOptions = [
  { label: '1室', value: '1' },
  { label: '2室', value: '2' },
  { label: '3室', value: '3' },
  { label: '4室', value: '4' }
]

const form = ref<any>({
  district: '',
  area: 85,
  rooms: '3',
  halls: '2',
  orientation: '南',
  decorate: '精装',
  building_type: '板楼',
  floor_level: '中',
  has_vr: false,
  has_metro: false,
  has_elevator: true,
  '满两年': false,
  '满五年': false,
  '唯一住房': false
})

const result = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    const res: any = await getDistricts()
    if (Array.isArray(res)) {
      districts.value = res.map((d: any) => ({ label: d.label || d, value: d.value || d }))
    } else if (res && res.success) {
      districts.value = (res.data || []).map((d: any) => ({ label: d.label || d, value: d.value || d }))
    } else if (res && res.data) {
      districts.value = (res.data || []).map((d: any) => ({ label: d.label || d, value: d.value || d }))
    } else {
      districts.value = []
    }
  } catch (e: any) {
    console.error('获取区县失败', e)
    error.value = '获取区县失败，请检查后端或网络'
  } finally {
    loading.value = false
  }
})

async function onPredict() {
  error.value = null
  result.value = null
  if (!form.value.district) {
    error.value = '请先选择区县'
    return
  }
  loading.value = true
  try {
    const payload = {
      district: form.value.district,
      area: form.value.area,
      orientation: form.value.orientation,
      decorate: form.value.decorate,
      building_type: form.value.building_type,
      rooms: form.value.rooms,
      halls: form.value.halls,
      floor_level: form.value.floor_level,
      has_vr: form.value.has_vr,
      has_metro: form.value.has_metro,
      has_elevator: form.value.has_elevator,
      '满两年': form.value['满两年'],
      '满五年': form.value['满五年'],
      '唯一住房': form.value['唯一住房']
    }

    const resp: any = await predictPrice(payload)
    if (resp && resp.success) {
      result.value = resp.data
    } else if (resp) {
      result.value = resp
    }
  } catch (e: any) {
    console.error('预测失败', e)
    error.value = '预测失败，请查看控制台日志'
  } finally {
    loading.value = false
  }
}

function reset() {
  form.value = {
    ...form.value,
    district: '',
    area: 85,
    rooms: '3',
    has_vr: false,
    has_metro: false
  }
  result.value = null
  error.value = null
}
</script>

<style scoped>
.predict-page {
  padding: 16px;
}
.title {
  margin-bottom: 12px;
}
.actions {
  display: flex;
  gap: 12px;
}
.result {
  margin-top: 12px;
}
.hint {
  color: var(--n-text-3);
  margin-top: 8px;
}
.error {
  color: var(--n-danger);
}
</style>