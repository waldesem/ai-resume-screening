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
const report = ref<ScreeningReport | null>(null);
const health = ref<"checking" | "online" | "offline">("checking");
const reportAnchor = ref<HTMLElement | null>(null);

const healthLabel = computed(() => {
  switch (health.value) {
    case "online":
      return "Backend доступен";
    case "offline":
      return "Backend недоступен";
    default:
      return "Проверяем backend…";
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
        <UChip
          size="xl"
          :color="
            health == 'online'
              ? 'success'
              : health == 'offline'
                ? 'error'
                : 'warning'
          "
        >
          <UButton
            :label="healthLabel"
            :title="healthTitle"
            icon="i-lucide-refresh-ccw"
            trailing-icon
            variant="outline"
            color="neutral"
            size="sm"
            @click="refreshHealth"
          />
        </UChip>
      </template>
    </UHeader>

    <UContainer class="pt-4">
      <UMain>
        <UCard
          title="Проверка анкеты"
          description="Загрузите JSON-анкету кандидата или вставьте её текстом."
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

        <div ref="reportAnchor">
          <ReportView v-if="report" :report="report" />
        </div>
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
