<script setup lang="ts">
import { computed } from "vue";

import type { Fit } from "../types";
import {
  confidenceLabel,
  formatYears,
  verdictClass,
  verdictLabel,
} from "../utils/format";

const props = defineProps<{ fit: Fit }>();

const verdict = computed(() => props.fit.verdict ?? "unknown");
const score = computed(() => {
  const value = props.fit.score;
  if (value === null || value === undefined) {
    return 0;
  }
  return Math.min(100, Math.max(0, value));
});

const strengths = computed(() => props.fit.strengths ?? []);
const gaps = computed(() => props.fit.gaps ?? []);
const matched = computed(() => props.fit.matched_requirements ?? []);
const unmatched = computed(() => props.fit.unmatched_requirements ?? []);
const hasYears = computed(
  () =>
    props.fit.relevant_experience_years != null ||
    props.fit.required_experience_years != null,
);
</script>

<template>
  <div class="grid gap-3 pt-2">
    <div class="inline-block font-semibold text-lg">
      <span class="bg-gray-100 px-2 rounded-lg">2</span>
      Соответствие должности
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-4">
      <UCard variant="soft">
        <div class="font-semibold text-secondary pb-1">РЕШЕНИЕ</div>
        <UBadge
          :color="verdictClass(verdict)"
          size="lg"
          :label="verdictLabel(verdict)"
        />
      </UCard>

      <div class="sm:col-span-2">
        <UCard variant="soft">
          <div class="font-semibold text-secondary">ШКАЛА СООТВЕТСТВИЯ</div>
          <UProgress :model-value="score" :color="verdictClass(verdict)" status />
        </UCard>
      </div>

      <UCard variant="soft">
        <div class="font-semibold text-secondary pb-1">УВЕРЕННОСТЬ</div>
        <div class="font-semibold text-secondary">
          {{ confidenceLabel(fit.confidence) }}
        </div>
      </UCard>
    </div>

    <UAlert v-if="fit.summary" color="info" :title="fit.summary" />

    <div v-if="hasYears" class="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <UCard variant="subtle">
        <div class="font-semibold text-secondary">Релевантный опыт</div>
        <div class="font-semibold text-secondary">
          {{ formatYears(fit.relevant_experience_years) }}
        </div>
      </UCard>
      <UCard variant="subtle">
        <div class="font-semibold text-secondary">Требуется</div>
        <div class="font-semibold text-secondary">
          {{ formatYears(fit.required_experience_years) }}
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
      <UCard>
        <div class="flex items-center gap-2 py-2">
          <UIcon name="i-lucide-rocket" />
          <div class="font-semibold text-secondary">Сильные стороны</div>
        </div>
        <ul>
          <li v-for="item in strengths" :key="item">{{ item }}</li>
          <li v-if="!strengths.length" class="list-empty">—</li>
        </ul>

        <div class="flex items-center gap-2 py-2">
          <UIcon name="i-lucide-thumbs-up" />
          <div class="font-semibold text-secondary">Совпавшие требования</div>
        </div>
        <ul>
          <li v-for="item in matched" :key="item">{{ item }}</li>
          <li v-if="!matched.length">—</li>
        </ul>
      </UCard>

      <UCard>
        <div class="flex items-center gap-2 py-2">
          <UIcon name="i-lucide-triangle-alert" />
          <div class="font-semibold text-secondary">Пробелы / риски</div>
        </div>
        <ul>
          <li v-for="item in gaps" :key="item">{{ item }}</li>
          <li v-if="!gaps.length">—</li>
        </ul>

        <div class="flex items-center gap-2 py-2">
          <UIcon name="i-lucide-ban" />
          <div class="font-semibold text-secondary">Несовпавшие требования</div>
        </div>
        <ul>
          <li v-for="item in unmatched" :key="item">{{ item }}</li>
          <li v-if="!unmatched.length">—</li>
        </ul>
      </UCard>
    </div>
  </div>
</template>
