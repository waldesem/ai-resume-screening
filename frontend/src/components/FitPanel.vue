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
const scoreWidth = computed(
  () => `${Math.max(0, Math.min(100, score.value ?? 0))}%`,
);

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
  <section class="section">
    <div class="section-header">
      <h3 class="section-title">
        <span class="section-index">2</span>
        Соответствие должности
      </h3>
    </div>

    <div class="fit-grid">
      <div class="fit-cell">
        <span class="metric-label">Вердикт</span>
        <UBadge :color="verdictClass(verdict)">
          {{ verdictLabel(verdict) }}
        </UBadge>
      </div>

      <div class="fit-cell fit-score">
        <div class="fit-score-head">
          <span class="metric-label">Оценка соответствия</span>
          <strong>{{ score !== null ? `${score}%` : "—" }}</strong>
        </div>
        <div class="progress">
          <div
            class="progress-bar"
            :class="`progress-${verdictClass(verdict)}`"
            :style="{ width: scoreWidth }"
          ></div>
        </div>
      </div>

      <div class="fit-cell">
        <span class="metric-label">Уверенность</span>
        <span class="fit-confidence-value">
          {{ confidenceLabel(fit.confidence) }}
        </span>
      </div>
    </div>

    <p v-if="fit.summary" class="fit-summary">{{ fit.summary }}</p>

    <div v-if="hasYears" class="years-row">
      <div class="year-item">
        <span class="metric-label">Релевантный опыт</span>
        <strong>{{ formatYears(fit.relevant_experience_years) }}</strong>
      </div>
      <div class="year-item">
        <span class="metric-label">Требуется</span>
        <strong>{{ formatYears(fit.required_experience_years) }}</strong>
      </div>
    </div>

    <div class="fit-columns">
      <div class="list-card">
        <h4 class="list-title">
          <UIcon name="i-lucide-check" />
          Сильные стороны
        </h4>
        <ul class="list">
          <li v-for="item in strengths" :key="item">{{ item }}</li>
          <li v-if="!strengths.length" class="list-empty">—</li>
        </ul>

        <h4 class="list-title">
          <UIcon name="i-lucide-target" />
          Совпавшие требования
        </h4>
        <ul class="list">
          <li v-for="item in matched" :key="item">{{ item }}</li>
          <li v-if="!matched.length" class="list-empty">—</li>
        </ul>
      </div>

      <div class="list-card">
        <h4 class="list-title">
          <UIcon name="i-lucide-warning" />
          Пробелы / риски
        </h4>
        <ul class="list">
          <li v-for="item in gaps" :key="item">{{ item }}</li>
          <li v-if="!gaps.length" class="list-empty">—</li>
        </ul>

        <h4 class="list-title">
          <UIcon name="i-lucide-x" />
          Несовпавшие требования
        </h4>
        <ul class="list">
          <li v-for="item in unmatched" :key="item">{{ item }}</li>
          <li v-if="!unmatched.length" class="list-empty">—</li>
        </ul>
      </div>
    </div>
  </section>
</template>
