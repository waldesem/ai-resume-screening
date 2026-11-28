<script setup lang="ts">
import { computed } from "vue";
import { useDateFormat } from "@vueuse/core";

import type { CandidateFacts, ScreeningReport } from "../types";
import { downloadJson } from "../utils/download";
import { formatYears, verdictClass } from "../utils/format";

import ContradictPanel from "./ContradictPanel.vue";
import FitPanel from "./FitPanel.vue";

interface CardFields<T> {
  title: string;
  description: (row: T) => string;
}

const props = defineProps<{ report: ScreeningReport }>();

const candidate = computed(() => props.report.candidate ?? {});
const contradictions = computed(() => props.report.contradictions ?? {});
const fit = computed(() => props.report.fit ?? {});
const errors = computed(() => props.report.analysis_errors ?? []);
const generatedAt = useDateFormat(
  computed(() => props.report.generated_at),
  "YYYY-MM-DD (ddd)",
  { locales: "ru-RU" },
);
const prettyJson = computed(() => JSON.stringify(props.report, null, 2));

function saveJson(): void {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  downloadJson(props.report, `candidate_report_${stamp}.json`);
}

const dataCard: CardFields<CandidateFacts>[] = [
  {
    title: "Возраст",
    description: (row) => String(row.age ?? "—"),
  },
  {
    title: "Стаж по датам",
    description: (row) => formatYears(row.career_span_years),
  },
  {
    title: "Образование",
    description: (row) => String(row.education_count ?? 0),
  },
  {
    title: "Мест работы",
    description: (row) => String(row.experience_count ?? 0),
  },
];
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex justify-between">
        <div>
          <div class="text-primary font-semibold">ОТЧЕТ О ПРОВЕРКЕ</div>
          <div class="text-xl font-semibold">
            {{ candidate.full_name || "Кандидат без имени" }}
          </div>
          <div class="text-secondary">
            {{ candidate.position_name || "Должность не указана" }}
            <span v-if="candidate.department">
              · {{ candidate.department }}</span
            >
          </div>
        </div>

        <div class="text-sm text-secondary">
          <div v-if="report.model">Модель: {{ report.model }}</div>
          <div v-if="generatedAt">Сформирован: {{ generatedAt }}</div>
        </div>
      </div>
    </template>

    <div class="grid gap-3">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <UCard
          v-for="(data, idx) in dataCard"
          :key="`${idx}-${data.title}`"
          variant="subtle"
          :title="data.title"
          :description="data.description(candidate)"
        />
      </div>

      <ContradictPanel :contradictions="contradictions" />

      <FitPanel :fit="fit" />

      <div class="inline-block font-semibold text-lg pt-2">
        <span class="bg-elevated px-2 rounded-lg">3</span>
        Рекомендация
      </div>
      <UAlert
        icon="i-lucide-lightbulb"
        :color="verdictClass(fit.verdict)"
        :title="report.recommendation || '—'"
      />

      <UAlert
        v-if="errors.length"
        title="Часть LLM-анализа не выполнена:"
        color="error"
      >
        <template #description>
          <ul>
            <li v-for="(error, index) in errors" :key="index">
              <code>{{ error.stage || "unknown" }}</code
              >: {{ error.message }}
            </li>
          </ul>
        </template>
      </UAlert>

      <UCollapsible class="w-full no-print">
        <UButton
          label="Полный отчёт (JSON)"
          color="secondary"
          variant="subtle"
          trailing-icon="i-lucide-chevron-down"
          block
        />
        <template #content>
          <div class="relative pt-3">
            <UButton
              class="absolute right-0 top-3 z-10"
              icon="i-lucide-download"
              size="sm"
              aria-label="Скачать отчёт в JSON"
              @click="saveJson"
            />
            <pre
              class="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-elevated p-3 pt-10 text-xs"
            >{{ prettyJson }}</pre>
          </div>
        </template>
      </UCollapsible>
    </div>
  </UCard>
</template>
