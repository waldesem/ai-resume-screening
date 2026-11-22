<script setup lang="ts">
import { computed } from "vue";

import type { ScreeningReport } from "../types";
import { downloadJson } from "../utils/download";
import {
  fileTimestamp,
  formatDateTime,
  formatYears,
  verdictClass,
} from "../utils/format";
import AppIcon from "./AppIcon.vue";
import ContradictionsPanel from "./ContradictionsPanel.vue";
import FitPanel from "./FitPanel.vue";

const props = defineProps<{ report: ScreeningReport }>();

const candidate = computed(() => props.report.candidate ?? {});
const contradictions = computed(() => props.report.contradictions ?? {});
const fit = computed(() => props.report.fit ?? {});
const errors = computed(() => props.report.analysis_errors ?? []);
const generatedAt = computed(() => formatDateTime(props.report.generated_at));
const prettyJson = computed(() => JSON.stringify(props.report, null, 2));

function saveJson(): void {
  downloadJson(
    props.report,
    `candidate_report_${fileTimestamp()}.json`,
  );
}
</script>

<template>
  <section class="report">
    <div class="report-header">
      <div class="report-identity">
        <p class="eyebrow">Отчёт о проверке</p>
        <h2 class="report-title">
          {{ candidate.full_name || "Кандидат без имени" }}
        </h2>
        <p class="muted report-subtitle">
          {{ candidate.position_name || "Должность не указана" }}
          <span v-if="candidate.department"> · {{ candidate.department }}</span>
        </p>
      </div>

      <div class="report-meta">
        <span v-if="report.model" class="meta-item">
          Модель: {{ report.model }}
        </span>
        <span v-if="generatedAt" class="meta-item">
          Сформирован: {{ generatedAt }}
        </span>
      </div>
    </div>

    <div class="metrics-grid">
      <div class="metric">
        <span class="metric-label">Возраст</span>
        <span class="metric-value">{{ candidate.age ?? "—" }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Стаж по датам</span>
        <span class="metric-value">
          {{ formatYears(candidate.career_span_years) }}
        </span>
      </div>
      <div class="metric">
        <span class="metric-label">Образование</span>
        <span class="metric-value">{{ candidate.education_count ?? 0 }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Мест работы</span>
        <span class="metric-value">{{ candidate.experience_count ?? 0 }}</span>
      </div>
    </div>

    <ContradictionsPanel :contradictions="contradictions" />
    <FitPanel :fit="fit" />

    <section class="section">
      <div class="section-header">
        <h3 class="section-title">
          <span class="section-index">3</span>
          Рекомендация
        </h3>
      </div>
      <div
        class="recommendation"
        :class="`recommendation-${verdictClass(fit.verdict)}`"
      >
        <AppIcon class="recommendation-icon" name="bulb" :size="20" />
        <p>{{ report.recommendation || "—" }}</p>
      </div>
    </section>

    <div v-if="errors.length" class="alert alert-error">
      <strong>Часть LLM-анализа не выполнена:</strong>
      <ul class="errors-list">
        <li v-for="(error, index) in errors" :key="index">
          <code>{{ error.stage || "unknown" }}</code>: {{ error.message }}
        </li>
      </ul>
    </div>

    <details class="json-block">
      <summary>Полный отчёт (JSON)</summary>
      <div class="json-toolbar">
        <button
          class="btn btn-secondary btn-small"
          type="button"
          @click="saveJson"
        >
          <AppIcon name="download" :size="16" />
          Скачать JSON
        </button>
      </div>
      <pre class="json-content">{{ prettyJson }}</pre>
    </details>
  </section>
</template>
