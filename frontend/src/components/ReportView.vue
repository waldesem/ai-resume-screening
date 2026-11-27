<script setup lang="ts">
import { computed } from "vue";
import { useDateFormat, useNow } from "@vueuse/core";

import type { ScreeningReport } from "../types";
import { downloadJson } from "../utils/download";
import { formatYears, verdictClass } from "../utils/format";
import ContradictionsPanel from "./ContradictionsPanel.vue";
import FitPanel from "./FitPanel.vue";

const props = defineProps<{ report: ScreeningReport }>();

const candidate = computed(() => props.report.candidate ?? {});
const contradictions = computed(() => props.report.contradictions ?? {});
const fit = computed(() => props.report.fit ?? {});
const errors = computed(() => props.report.analysis_errors ?? []);
const generatedAt = useDateFormat(
  props.report.generated_at,
  "YYYY-MM-DD (ddd)",
  {
    locales: "ru-RU",
  },
);
const prettyJson = computed(() => JSON.stringify(props.report, null, 2));

function saveJson(): void {
  downloadJson(
    props.report,
    `candidate_report_${useDateFormat(useNow(), "YYYY-MM-DD HH:mm:ss")}.json`,
  );
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex justify-between">
        <div>
          <div class="text-blue-600 font-semibold">ОТЧЕТ О ПРОВЕРКЕ</div>
          <div class="text-xl font-semibold">
            {{ candidate.full_name || "Кандидат без имени" }}
          </div>
          <div class="text-gray-600">
            {{ candidate.position_name || "Должность не указана" }}
            <span v-if="candidate.department">
              · {{ candidate.department }}</span
            >
          </div>
        </div>

        <div class="text-sm text-gray-600">
          <div v-if="report.model">Модель: {{ report.model }}</div>
          <div v-if="generatedAt">Сформирован: {{ generatedAt }}</div>
        </div>
      </div>
    </template>

    <div class="grid grid-rows gap-3">
      <div class="grid grid-cols-4 gap-3">
        <UCard
          v-for="(data, idx) in [
            {
              label: 'Возраст',
              value: candidate.age ?? '—',
            },
            {
              label: 'Стаж по датам',
              value: formatYears(candidate.career_span_years),
            },
            {
              label: 'Образование',
              value: candidate.education_count ?? 0,
            },
            {
              label: 'Мест работы',
              value: candidate.experience_count ?? 0,
            },
          ]"
          :key="idx"
          variant="subtle"
          :title="data.label"
          :description="data.value.toString()"
        />
      </div>

      <ContradictionsPanel :contradictions="contradictions" />

      <FitPanel :fit="fit" />

      <div class="inline-block font-semibold text-lg pt-2">
        <span class="bg-gray-100 px-2 rounded-lg">3</span>
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
        :ui="{ root: 'bg-red-100' }"
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

      <UCollapsible class="relative w-full">
        <UButton
          label="Полный отчёт (JSON)"
          color="neutral"
          variant="subtle"
          trailing-icon="i-lucide-chevron-down"
          block
        />
        <template #content>
          <UButton
            class="absolute top-15 right-5"
            icon="i-lucide-download"
            size="sm"
            variant="outline"
            @click="saveJson"
          />
          <pre class="text-sm">{{ prettyJson }}</pre>
        </template>
      </UCollapsible>
    </div>
  </UCard>
</template>
