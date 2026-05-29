<script setup lang="ts">
import type { ActivityDay } from '@pjasaver/shared-types'

const props = defineProps<{
  data: ActivityDay[]
  loading?: boolean
}>()

const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const total = computed(() => props.data.reduce((s, d) => s + d.count, 0))
const maxCount = computed(() => Math.max(...props.data.map(d => d.count), 1))

function getLevel(count: number): number {
  if (count === 0) return 0
  const ratio = count / maxCount.value
  if (ratio <= 0.25) return 1
  if (ratio <= 0.5) return 2
  if (ratio <= 0.75) return 3
  return 4
}

const weeks = computed(() => {
  if (!props.data.length) return []
  const result: { day: number; level: number; date: string; count: number; }[][] = []
  let week: { day: number; level: number; date: string; count: number; }[] = []

  for (const item of props.data) {
    const d = new Date(item.date)
    const dayOfWeek = d.getDay()
    const adjustedDay = dayOfWeek === 0 ? 6 : dayOfWeek - 1

    if (adjustedDay === 0 && week.length > 0) {
      result.push(week)
      week = []
    }

    week.push({
      day: adjustedDay,
      level: getLevel(item.count),
      date: item.date,
      count: item.count,
    })
  }

  if (week.length > 0) result.push(week)
  return result
})
</script>

<template>
  <div class="card p-5">
    <div class="flex items-center gap-2 mb-4">
      <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
      </svg>
      <span class="text-sm font-medium">{{ total }} {{ total === 1 ? 'активность' : 'активностей' }} за последний год</span>
    </div>

    <div v-if="loading" class="flex justify-center py-8">
      <svg class="w-5 h-5 text-secondary animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <div v-else-if="!weeks.length" class="text-sm text-secondary text-center py-8">
      Нет активности за этот период
    </div>

    <div v-else class="overflow-x-auto pb-2">
      <div class="inline-flex gap-0.5">
        <!-- Day labels -->
        <div class="flex flex-col gap-[3px] mr-1 pt-0">
          <span class="text-[10px] text-secondary h-[13px] leading-[13px]">Пн</span>
          <span class="text-[10px] text-secondary h-[13px] leading-[13px]">Ср</span>
          <span class="text-[10px] text-secondary h-[13px] leading-[13px]">Пт</span>
        </div>

        <!-- Grid -->
        <div class="flex gap-[3px]">
          <div
            v-for="(week, wi) in weeks"
            :key="wi"
            class="flex flex-col gap-[3px]"
          >
            <div
              v-for="day in 7"
              :key="day"
              class="w-[13px] h-[13px] rounded-sm"
              :class="{
                'bg-[var(--color-heatmap-empty)]': !week.find(w => w.day === day - 1),
                'bg-primary/10': week.find(w => w.day === day - 1)?.level === 1,
                'bg-primary/25': week.find(w => w.day === day - 1)?.level === 2,
                'bg-primary/50': week.find(w => w.day === day - 1)?.level === 3,
                'bg-primary': week.find(w => w.day === day - 1)?.level === 4,
              }"
              :title="week.find(w => w.day === day - 1)
                ? `${week.find(w => w.day === day - 1)?.count} активностей — ${week.find(w => w.day === day - 1)?.date}`
                : ''"
            />
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-1 mt-3 justify-end text-[10px] text-secondary">
        <span>Меньше</span>
        <div class="w-[13px] h-[13px] rounded-sm bg-[var(--color-heatmap-empty)]" />
        <div class="w-[13px] h-[13px] rounded-sm bg-primary/10" />
        <div class="w-[13px] h-[13px] rounded-sm bg-primary/25" />
        <div class="w-[13px] h-[13px] rounded-sm bg-primary/50" />
        <div class="w-[13px] h-[13px] rounded-sm bg-primary" />
        <span>Больше</span>
      </div>
    </div>
  </div>
</template>
