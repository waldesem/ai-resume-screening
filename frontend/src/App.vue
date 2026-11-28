<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { checkHealth, screenCandidate } from "./api";

import type { ScreeningReport } from "./types";

import ReportView from "./components/ReportView.vue";
import ScreenForm from "./components/ScreenForm.vue";

const candidateJson = ref("");
const loading = ref(false);
const error = ref("");
const success = ref("");
const report = ref<ScreeningReport | null>(null);
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
  <UContainer>
    <header class="flex items-center justify-between my-5 no-print">
      <div class="flex items-center gap-2 text-primary">
        <UIcon name="i-lucide-cpu-ai" size="32" />
        <div class="text-xl font-bold text-error">Resume Screening</div>
      </div>
      <UButton
        :title="healthLabel"
        :aria-label="healthLabel"
        :icon="
          health == 'online'
            ? 'i-lucide-bot'
            : health == 'offline'
              ? 'i-lucide-bot-off'
              : 'i-lucide-rotate-cw-clock'
        "
        :label="health"
        :color="
          health == 'online'
            ? 'info'
            : health == 'offline'
              ? 'error'
              : 'warning'
        "
        variant="outline"
        class="rounded-xl"
        @click="refreshHealth"
      />
    </header>
    <UMain>
      <UCard
        title="Проверка анкеты"
        description="Загрузите JSON-файл анкеты или вставьте JSON текстом"
        class="no-print"
      >
        <ScreenForm
          :candidate-json="candidateJson"
          :loading="loading"
          @update:candidate-json="candidateJson = $event"
          @submit="onSubmit"
          @error="onFormError"
          @clear-error="clearMessages"
        />
      </UCard>

      <div aria-live="polite" class="no-print pb-3">
        <UAlert v-if="error" :title="error" color="error" />
        <UAlert v-if="success && !error" :title="success" color="success" />
      </div>

      <UCard v-if="!report && !loading" class="my-4 text-center">
        <UIcon name="i-lucide-file-search" class="mx-auto text-secondary" />
        <p class="mt-2 font-semibold">Отчёт появится здесь</p>
        <p class="text-sm text-secondary">
          Загрузите JSON-анкету и нажмите «Проверить анкету».
        </p>
      </UCard>

      <div ref="reportAnchor" class="scroll-mt-4">
        <ReportView v-if="report" :report="report" />
      </div>
    </UMain>

    <UFooter class="text-sm text-secondary no-print">
      <template #left>
        <span>AI Resume Screening</span>
      </template>
      <template #right>
        <span>FastAPI · Ollama · Qwen · Vue</span>
      </template>
    </UFooter>
  </UContainer>
</template>
