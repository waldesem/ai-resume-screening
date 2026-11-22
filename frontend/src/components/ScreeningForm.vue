<script setup lang="ts">
import { computed, ref } from "vue";

import { parseCandidate, readCandidateFile } from "../utils/candidate";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{
  candidateJson: string;
  fileName: string;
  loading: boolean;
}>();

const emit = defineEmits<{
  "update:candidate-json": [value: string];
  "update:file-name": [value: string];
  submit: [candidate: unknown];
  error: [message: string];
  "clear-error": [];
}>();

const dragging = ref(false);

const candidateModel = computed({
  get: () => props.candidateJson,
  set: (value: string) => {
    emit("update:candidate-json", value);
    emit("clear-error");
  },
});

const hasFile = computed(() => Boolean(props.fileName));

const jsonStatus = computed(() => {
  const text = props.candidateJson.trim();
  if (!text) {
    return { state: "empty", label: "JSON не загружен" };
  }
  try {
    parseCandidate(text);
    return { state: "ok", label: "JSON корректен" };
  } catch (error) {
    return { state: "error", label: (error as Error).message };
  }
});

async function applyFile(file: File): Promise<void> {
  try {
    const text = await readCandidateFile(file);
    emit("update:candidate-json", text);
    emit("update:file-name", file.name);
    emit("clear-error");
  } catch (error) {
    emit("error", (error as Error).message);
  }
}

async function onFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) {
    await applyFile(file);
  }
  input.value = "";
}

async function onDrop(event: DragEvent): Promise<void> {
  dragging.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) {
    await applyFile(file);
  }
}

function removeFile(): void {
  emit("update:file-name", "");
}

function submit(): void {
  try {
    const candidate = parseCandidate(props.candidateJson);
    emit("clear-error");
    emit("submit", candidate);
  } catch (error) {
    emit("error", (error as Error).message);
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <div class="form-grid">
      <div class="field">
        <label class="field-label" for="candidate-json">
          Анкета кандидата (JSON)
        </label>

        <label
          class="dropzone"
          :class="{ 'is-dragging': dragging }"
          @dragenter.prevent="dragging = true"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <input
            id="candidate-file"
            type="file"
            accept=".json,application/json"
            hidden
            @change="onFileChange"
          />
          <span class="dropzone-icon">
            <AppIcon name="paperclip" :size="22" />
          </span>
          <span class="dropzone-text">
            Перетащите JSON-файл сюда или <strong>выберите файл</strong>
          </span>
          <span class="field-hint">Поддерживаются UTF-8 и Windows-1251</span>
        </label>

        <div v-if="hasFile" class="file-chip">
          <span class="file-chip-name">
            <AppIcon name="file" :size="14" />
            <span class="file-chip-text">{{ fileName }}</span>
          </span>
          <button
            class="file-remove"
            type="button"
            aria-label="Убрать файл"
            @click="removeFile"
          >
            ×
          </button>
        </div>

        <textarea
          id="candidate-json"
          v-model="candidateModel"
          class="textarea textarea-code"
          rows="14"
          spellcheck="false"
          placeholder='{"positionName": "...", "experience": [], ...}'
        ></textarea>

        <p class="json-status" :class="`json-status-${jsonStatus.state}`">
          {{ jsonStatus.label }}
        </p>
      </div>
    </div>

    <div class="form-actions">
      <button class="btn btn-primary" type="submit" :disabled="loading">
        <span v-if="loading" class="spinner spinner-small"></span>
        <AppIcon v-else name="search" :size="16" />
        <span>{{ loading ? "Анализируем анкету…" : "Проверить анкету" }}</span>
      </button>
      <span class="field-hint">
        Анализ с локальной LLM может занять несколько минут.
      </span>
    </div>
  </form>
</template>
