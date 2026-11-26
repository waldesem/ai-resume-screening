<script setup lang="ts">
import { computed, ref } from "vue";

import { parseCandidate, readCandidateFile } from "../utils/candidate";

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

const file = ref<File>();

const jsonStatus = computed(() => {
  const text = props.candidateJson.trim();
  if (!text) {
    return { state: "neutral", label: "JSON не загружен" };
  }
  try {
    parseCandidate(text);
    return { state: "success", label: "JSON корректен" };
  } catch (error) {
    return { state: "error", label: (error as Error).message };
  }
});

async function screen() {
  if (file.value) {
    try {
      const text = await readCandidateFile(file.value);
      emit("update:candidate-json", text);
      emit("update:file-name", file.value.name);
      emit("clear-error");
    } catch (error) {
      emit("error", (error as Error).message);
    }
  }
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
  <UFormField @change.prevent="screen" @submit.prevent="submit">
    <UFileUpload
      v-model="file"
      accept=".json"
      class="w-full"
      label="Выберите/перенесите JSON-файл"
      description="Поддерживаются UTF-8 и Windows-1251"
    />
    <div class="flex justify-between pt-4">
      <UBadge :color="jsonStatus.state" variant="soft">
        {{ jsonStatus.label }}
      </UBadge>
      <UButton
        :disabled="loading"
        :loading="loading"
        variant="outline"
        type="submit"
      >
        <span>{{
          loading
            ? "Анализируем анкету… Это может занять несколько минут."
            : "Проверить анкету"
        }}</span>
      </UButton>
    </div>
  </UFormField>
</template>
