<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { parseCandidate, readCandidateFile } from "../utils/candidate";

const props = defineProps<{
  candidateJson: string;
  loading: boolean;
}>();

const emit = defineEmits<{
  "update:candidate-json": [value: string];
  submit: [candidate: unknown];
  error: [message: string];
  "clear-error": [];
}>();

const file = ref<File | null>(null);

const jsonStatus = computed(() => {
  const text = props.candidateJson.trim();
  if (!text) {
    return { state: "secondary", label: "JSON не загружен" };
  }
  try {
    parseCandidate(text);
    return { state: "success", label: "JSON корректен" };
  } catch (error) {
    return { state: "error", label: (error as Error).message };
  }
});

watch(file, async (selected) => {
  if (!selected) {
    return;
  }
  try {
    const text = await readCandidateFile(selected);
    emit("update:candidate-json", text);
    emit("clear-error");
  } catch (error) {
    emit("error", (error as Error).message);
  }
});

function updateJson(value: string | number): void {
  emit("update:candidate-json", String(value));
  emit("clear-error");
}

function submit() {
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
  <UForm :state="{ candidateJson }" @submit="submit">
    <div class="grid gap-4">
      <UFileUpload
        v-model="file"
        accept=".json,application/json"
        class="w-full"
        label="Выберите/перенесите JSON-файл"
        description="Поддерживаются UTF-8, UTF-16 и Windows-1251"
        :disabled="loading"
      />

      <UFormField label="Или вставьте JSON анкеты">
        <UTextarea
          :model-value="candidateJson"
          :rows="8"
          :leading="loading"
          variant="subtle"
          class="w-full font-mono text-xs"
          placeholder='{"positionName": "...", "experience": []}'
          @update:model-value="updateJson"
        />
      </UFormField>

      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <UBadge :color="jsonStatus.state">
            {{ jsonStatus.label }}
          </UBadge>
          <span v-if="file" class="text-sm text-secondary">
            {{ file.name }}
          </span>
        </div>
        <UButton
          :disabled="loading || !candidateJson.trim()"
          :loading="loading"
          type="submit"
        >
          {{
            loading
              ? "Анализируем анкету… Это может занять несколько минут."
              : "Проверить анкету"
          }}
        </UButton>
      </div>
    </div>
  </UForm>
</template>
