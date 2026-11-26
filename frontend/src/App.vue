<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { checkHealth, screenCandidate } from "./api";
import ReportView from "./components/ReportView.vue";
import ScreeningForm from "./components/ScreeningForm.vue";
import type { ScreeningReport } from "./types";

const candidateJson = ref("");
const fileName = ref("");
const loading = ref(false);
const error = ref("");
const success = ref("");
const report = ref<ScreeningReport | null>({
  generated_at: "2026-11-22T13:00:00",
  model: "Qwen3-8B-GGUF:Q4_K_M",
  candidate: {
    full_name: "Иванов Пётр",
    position_name: "Ведущий аналитик данных",
    department: "Департамент аналитики",
    age: 33,
    career_start: "2014-09-01",
    career_span_years: 12.2,
    has_job: true,
    education_count: 2,
    experience_count: 2,
  },
  contradictions: {
    has_contradictions: true,
    counts: { high: 1, medium: 2, low: 0 },
    items: [
      {
        severity: "high",
        code: "experience_0_too_early",
        title: "Работа началась в слишком раннем возрасте",
        description: "…",
        fields: ["experience[0].beginDate", "birthday"],
        source: "rule",
      },
    ],
    summary: "…",
  },
  fit: {
    verdict: "partially_suitable",
    score: 72,
    summary: "…",
    strengths: ["…"],
    gaps: ["…"],
    matched_requirements: ["…"],
    unmatched_requirements: ["…"],
    relevant_experience_years: 12.2,
    required_experience_years: 3.0,
    confidence: "high",
  },
  recommendation: "…",
  analysis_errors: [],
});
const health = ref<"checking" | "online" | "offline">("checking");
const reportAnchor = ref<HTMLElement | null>(null);

const healthLabel = computed(() => {
  switch (health.value) {
    case "online":
      return "Сервер доступен";
    case "offline":
      return "Сервер недоступен";
    default:
      return "Проверяем сервер";
  }
});

const healthTitle = computed(() =>
  health.value === "offline"
    ? "FastAPI не отвечает. Запустите backend и обновите проверку."
    : "Состояние соединения с FastAPI",
);

onMounted(refreshHealth);

async function refreshHealth(): Promise<void> {
  health.value = "checking";
  health.value = (await checkHealth()) ? "online" : "offline";
}

function clearMessages(): void {
  error.value = "";
  success.value = "";
}

function onFormError(message: string): void {
  error.value = message;
  success.value = "";
}

async function onSubmit(candidate: unknown): Promise<void> {
  clearMessages();
  loading.value = true;

  try {
    const result = await screenCandidate(candidate);
    report.value = result;
    success.value = "Анкета обработана.";
    await nextTick();
    reportAnchor.value?.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <UApp>
    <UHeader title="AI Resume Screening">
      <template #right>
        <UButton
          class="rounded-full"
          :label="healthLabel"
          :title="healthTitle"
          icon="i-lucide-refresh-ccw"
          variant="outline"
          :color="
            health == 'online'
              ? 'success'
              : health == 'offline'
                ? 'error'
                : 'warning'
          "
          size="xs"
          @click="refreshHealth"
        />
      </template>
    </UHeader>

    <UContainer>
      <UMain>
        <UCard
          class="my-4"
          title="Проверка анкеты"
          description="Загрузите JSON-анкету кандидата"
        >
          <ScreeningForm
            :candidate-json="candidateJson"
            :file-name="fileName"
            :loading="loading"
            @update:candidate-json="candidateJson = $event"
            @update:file-name="fileName = $event"
            @submit="onSubmit"
            @error="onFormError"
            @clear-error="clearMessages"
          />
        </UCard>

        <UAlert v-if="error" :title="error" color="error" />
        <UAlert v-if="success && !error" :title="success" color="success" />

        <!-- <div ref="reportAnchor"> -->
        <ReportView v-if="report" :report="report" />
        <!-- </div> -->
      </UMain>

      <UFooter class="text-muted">
        <template #left>
          <span>AI Resume Screening</span>
        </template>
        <template #right>
          <span>FastAPI · Ollama · Qwen · Vue</span>
        </template>
      </UFooter>
    </UContainer>
  </UApp>
</template>
