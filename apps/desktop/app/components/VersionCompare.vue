<script setup lang="ts">
interface Props {
  projectId: string
}

const props = defineProps<Props>()
const versions = useVersionsStore()
const toast = inject('toast') as { show: (msg: string, type: 'success' | 'error' | 'info') => void }

const ver1Id = ref('')
const ver2Id = ref('')
const result = ref<any>(null)
const loading = ref(false)

async function handleCompare() {
  if (!ver1Id.value || !ver2Id.value) return
  loading.value = true
  try {
    result.value = await useApiFetch(`/api/v1/projects/${props.projectId}/versions/compare`, {
      method: 'POST',
      body: { version_1_id: ver1Id.value, version_2_id: ver2Id.value },
    })
  } catch (e: any) {
    toast.show(e.message || 'Ошибка', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="grid grid-cols-2 gap-3">
      <div class="flex flex-col gap-1.5">
        <label class="text-sm font-medium">Версия 1</label>
        <select
          v-model="ver1Id"
          class="rounded-lg input-control px-3 py-2 text-sm"
        >
          <option value="" disabled>Выберите версию</option>
          <option
            v-for="v in versions.sortedVersions"
            :key="v.id"
            :value="v.id"
          >
            v{{ v.version_number }} — {{ v.title }}
          </option>
        </select>
      </div>
      <div class="flex flex-col gap-1.5">
        <label class="text-sm font-medium">Версия 2</label>
        <select
          v-model="ver2Id"
          class="rounded-lg input-control px-3 py-2 text-sm"
        >
          <option value="" disabled>Выберите версию</option>
          <option
            v-for="v in versions.sortedVersions"
            :key="v.id"
            :value="v.id"
          >
            v{{ v.version_number }} — {{ v.title }}
          </option>
        </select>
      </div>
    </div>

    <UiButton :loading="loading" @click="handleCompare">Сравнить</UiButton>

    <div v-if="result" class="mt-4 space-y-2">
      <div class="card p-4">
        <h4 class="text-sm font-medium mb-2">Различия</h4>
        <div class="space-y-1 text-sm">
          <div class="flex items-center gap-2">
            <span class="text-secondary">Размер:</span>
            <span :class="result.differences.file_size_changed ? 'text-warning' : 'text-success'">
              {{ result.differences.file_size_changed ? 'Изменился' : 'Не изменился' }}
              <span v-if="result.differences.size_diff_bytes" class="text-xs">
                ({{ (result.differences.size_diff_bytes / 1024 / 1024).toFixed(2) }} MB разница)
              </span>
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-secondary">Хеш:</span>
            <span :class="result.differences.file_hash_changed ? 'text-warning' : 'text-success'">
              {{ result.differences.file_hash_changed ? 'Изменился' : 'Совпадает' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
