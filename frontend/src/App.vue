<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { checkHealth, screenCandidate } from "./api";
import AppIcon from "./components/AppIcon.vue";
import HistoryPanel from "./components/HistoryPanel.vue";
import ReportView from "./components/ReportView.vue";
import ScreeningForm from "./components/ScreeningForm.vue";
import { useHistory } from "./composables/useHistory";
import type { ScreeningReport } from "./types";

const candidateJson = ref("");
const fileName = ref("");
const loading = ref(false);
const error = ref("");
const success = ref("");
const report = ref<ScreeningReport | null>(null);
const health = ref<"checking" | "online" | "offline">("checking");
const reportAnchor = ref<HTMLElement | null>(null);

const { entries: history, add: addToHistory, clear: clearHistory } = useHistory();

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
    addToHistory(result);
    success.value = "Анкета обработана.";
    await nextTick();
    reportAnchor.value?.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

function onHistoryClear(): void {
  clearHistory();
  report.value = null;
  clearMessages();
}
</script>

<template>
  <div class="app">
    <header class="app-header">
      <div class="brand">
        <div class="brand-logo" aria-hidden="true">
          <AppIcon name="receipt" :size="30" :stroke-width="1.7" />
        </div>
        <div>
          <h1>Проверка анкеты кандидата</h1>
          <p class="muted brand-subtitle">
            Внутренние противоречия и соответствие целевой должности
          </p>
        </div>
      </div>

      <div class="status" :class="`status-${health}`" :title="healthTitle">
        <span class="status-dot"></span>
        <span>{{ healthLabel }}</span>
        <button
          class="status-refresh"
          type="button"
          aria-label="Проверить соединение"
          @click="refreshHealth"
        >
          <AppIcon name="refresh" :size="16" />
        </button>
      </div>
    </header>

    <main class="layout">
      <section class="card form-card">
        <div class="form-intro">
          <h2>Проверка анкеты</h2>
          <p class="muted">
            Загрузите JSON-анкету кандидата или вставьте её текстом.
          </p>
        </div>

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
      </section>

      <div v-if="error" class="alert alert-error" role="alert">
        {{ error }}
      </div>
      <div v-if="success && !error" class="alert alert-success" role="status">
        {{ success }}
      </div>

      <section v-if="loading" class="card loading-card" aria-live="polite">
        <span class="spinner"></span>
        <div>
          <strong>Анализируем анкету…</strong>
          <p class="muted">
            Проверяем противоречия и соответствие должности. Это может занять
            несколько минут.
          </p>
        </div>
      </section>

      <div ref="reportAnchor" class="report-anchor">
        <ReportView v-if="report" :report="report" />
      </div>

      <HistoryPanel
        v-if="history.length"
        :entries="history"
        @clear="onHistoryClear"
      />
    </main>

    <footer class="app-footer">
      <span>AI Resume Screening</span>
      <span class="muted">FastAPI · Ollama · Vue 3</span>
    </footer>
  </div>
</template>
