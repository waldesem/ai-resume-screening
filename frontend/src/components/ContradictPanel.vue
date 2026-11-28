<script setup lang="ts">
import { computed } from "vue";

import type { Contradictions } from "../types";
import { severityClass, severityLabel } from "../utils/format";

const props = defineProps<{ contradictions: Contradictions }>();

const counts = computed(
  () => props.contradictions.counts ?? { high: 0, medium: 0, low: 0 },
);
const items = computed(() => props.contradictions.items ?? []);
const hasFindings = computed(
  () =>
    items.value.length > 0 ||
    (counts.value.high ?? 0) +
      (counts.value.medium ?? 0) +
      (counts.value.low ?? 0) >
      0,
);
const severityCards = computed(() => [
  { label: "Критичные", value: counts.value.high ?? 0, color: "error" },
  { label: "Средние", value: counts.value.medium ?? 0, color: "warning" },
  { label: "Незначительные", value: counts.value.low ?? 0, color: "secondary" },
]);

function sourceLabel(source?: string): string {
  return source === "llm" ? "LLM" : "правило";
}
</script>

<template>
  <div class="grid gap-3 pt-2">
    <div class="inline-block font-semibold text-lg">
      <span class="bg-elevated px-2 rounded-lg">1</span>
      Внутренние противоречия
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <UAlert
        v-for="card in severityCards"
        :key="card.label"
        :color="card.color"
        :description="card.value.toString()"
        :title="card.label"
      />
    </div>

    <UAlert
      v-if="contradictions.summary"
      :title="contradictions.summary"
      color="primary"
    />

    <UAlert
      v-if="!hasFindings"
      icon="i-lucide-check-check"
      title="Формальных и смысловых противоречий не найдено."
      color="success"
    />

    <div v-else>
      <UCard
        v-for="(item, index) in items"
        :key="`${item.code ?? 'item'}-${index}`"
        :ui="{ header: 'border-none' }"
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
        <div
          v-if="item.fields?.length"
          class="mt-2 text-xs text-secondary"
        >
          Поля: {{ item.fields.join(", ") }}
        </div>
      </UCard>
    </div>
  </div>
</template>
