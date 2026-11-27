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
const score = computed(() => props.fit.score ?? null);

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
  <div class="grid grid-row gap-3 pt-2">
    <div class="inline-block font-semibold text-lg">
      <span class="bg-gray-100 px-2 rounded-lg">2</span>
      Соответствие должности
    </div>

    <div class="grid grid-cols-4 gap-3">
      <UCard variant="soft">
        <div class="font-semibold text-gray-500 pb-1">РЕШЕНИЕ</div>
        <UBadge
          :color="verdictClass(verdict)"
          size="lg"
          :label="verdictLabel(verdict)"
        />
      </UCard>

      <div class="col-span-2">
        <UCard variant="soft">
          <div class="font-semibold text-gray-500">ШКАЛА СООТВЕТСТВИЯ</div>
          <UProgress v-model="score" :color="verdictClass(verdict)" status />
        </UCard>
      </div>

      <UCard variant="soft">
        <div class="font-semibold text-gray-500 pb-1">УВЕРЕННОСТЬ</div>
        <div class="font-semibold text-gray-800">
          {{ confidenceLabel(fit.confidence) }}
        </div>
      </UCard>
    </div>

    <UAlert v-if="fit.summary" color="info" :title="fit.summary" />

    <div v-if="hasYears" class="grid grid-cols-2 gap-3">
      <UCard variant="subtle">
        <div class="font-semibold text-gray-500">Релевантный опыт</div>
        <div class="font-semibold text-gray-800">
          {{ formatYears(fit.relevant_experience_years) }}
        </div>
      </UCard>
      <UCard variant="subtle">
        <div class="font-semibold text-gray-500">Требуется</div>
        <div class="font-semibold text-gray-800">
          {{ formatYears(fit.required_experience_years) }}
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <UCard>
        <h4 class="list-title">
          <UIcon name="i-lucide-check" />
          Сильные стороны
        </h4>
        <ul>
          <li v-for="item in strengths" :key="item">{{ item }}</li>
          <li v-if="!strengths.length" class="list-empty">—</li>
        </ul>

        <h4 class="list-title">
          <UIcon name="i-lucide-target" />
          Совпавшие требования
        </h4>
        <ul>
          <li v-for="item in matched" :key="item">{{ item }}</li>
          <li v-if="!matched.length" class="list-empty">—</li>
        </ul>
      </UCard>

      <UCard>
        <h4 class="list-title">
          <UIcon name="i-lucide-warning" />
          Пробелы / риски
        </h4>
        <ul>
          <li v-for="item in gaps" :key="item">{{ item }}</li>
          <li v-if="!gaps.length" class="list-empty">—</li>
        </ul>

        <h4 class="list-title">
          <UIcon name="i-lucide-x" />
          Несовпавшие требования
        </h4>
        <ul>
          <li v-for="item in unmatched" :key="item">{{ item }}</li>
          <li v-if="!unmatched.length" class="list-empty">—</li>
        </ul>
      </UCard>
    </div>
  </div>
</template>
