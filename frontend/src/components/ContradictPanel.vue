<script setup lang="ts">
import { computed } from "vue";

import type { Contradictions } from "../types";
import { severityClass, severityLabel } from "../utils/format";

const props = defineProps<{ contradictions: Contradictions }>();

const counts = computed(
  () => props.contradictions.counts ?? { high: 0, medium: 0, low: 0 },
);
const items = computed(() => props.contradictions.items ?? []);

function sourceLabel(source?: string): string {
  return source === "llm" ? "LLM" : "правило";
}
</script>

<template>
  <div class="grid grid-row gap-3 pt-2">
    <div class="inline-block font-semibold text-lg">
      <span class="bg-gray-100 px-2 rounded-lg">1</span>
      Внутренние противоречия
    </div>

    <div class="grid grid-cols-3 gap-3">
      <UAlert
        v-for="(data, idx) in [
          {
            label: 'Критичные',
            value: counts.high ?? 0,
            bg: 'bg-red-100',
            text: 'text-red-800',
          },
          {
            label: 'Средние',
            value: counts.medium ?? 0,
            bg: 'bg-orange-100',
            text: 'text-orange-800',
          },
          {
            label: 'Незначительные',
            value: counts.low ?? 0,
            bg: 'bg-yellow-100',
            text: 'text-yellow-800',
          },
        ]"
        :key="idx"
        :ui="{ root: data.bg, title: data.text, description: data.text }"
        variant="subtle"
        :description="data.value.toString()"
        :title="data.label"
      />
    </div>

    <UAlert
      v-if="contradictions.summary"
      :title="contradictions.summary"
      :ui="{ root: 'bg-blue-100', title: 'text-blue-800' }"
    />

    <UAlert
      v-if="!items.length"
      icon="i-lucide-check-check"
      title="Формальных и смысловых противоречий не найдено."
      :ui="{
        root: 'bg-green-100',
        title: 'text-green-800',
        icon: 'text-green-800',
      }"
    />

    <div v-else>
      <UCard
        v-for="(item, index) in items"
        :key="index"
        :ui="{header: 'border-none'}"
      >
        <template #header>
          <div class="flex justify-between">
            <UBadge
              :label="severityLabel(item.severity)"
              :color="severityClass(item.severity)"
            />
            <div class="justify-self-start font-semibold">
              {{ item.title || "Противоречие" }}
            </div>
            <UBadge
              color="secondary"
              variant="soft"
              class="uppercase"
              :label="sourceLabel(item.source)"
            />
          </div>
        </template>

        <div v-if="item.description">
          {{ item.description }}
        </div>
      </UCard>
    </div>
  </div>
</template>
