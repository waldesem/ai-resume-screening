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
const report = ref<ScreeningReport | null>();
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
    <header class="flex items-center justify-between my-5">
      <div class="text-xl font-bold">AI Resume Screening</div>
      <UAvatar
        :text="healthLabel"
        :icon="
          health == 'online'
            ? 'i-lucide-wifi'
            : health == 'offline'
              ? 'i-lucide-wifi-off'
              : 'i-lucide-wifi-sync'
        "
        :color="
          health == 'online'
            ? 'success'
            : health == 'offline'
              ? 'error'
              : 'warning'
        "
      />
    </header>
    <UMain>
      <UCard
        class="my-4"
        title="Проверка анкеты"
        description="Загрузите JSON-анкету кандидата"
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

      <UAlert v-if="error" :title="error" color="error" />
      <UAlert v-if="success && !error" :title="success" color="success" />

      <div ref="reportAnchor">
      <ReportView v-if="report" :report="report" />
      </div>
    </UMain>

    <UFooter class="text-sm text-gray-600">
      <template #left>
        <span>AI Resume Screening</span>
      </template>
      <template #right>
        <span>FastAPI · Ollama · Qwen · Vue</span>
      </template>
    </UFooter>
  </UContainer>
</template>
