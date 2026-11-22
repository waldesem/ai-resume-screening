<script setup lang="ts">
import type { HistoryEntry } from "../types";
import { downloadHistoryCsv } from "../utils/download";
import { verdictClass } from "../utils/format";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ entries: HistoryEntry[] }>();
const emit = defineEmits<{ clear: [] }>();

function exportCsv(): void {
  downloadHistoryCsv(props.entries);
}

function confirmClear(): void {
  if (window.confirm("Очистить историю проверок?")) {
    emit("clear");
  }
}
</script>

<template>
  <section class="section history-section">
    <div class="section-header history-header">
      <h3 class="section-title">
        <AppIcon name="chart" :size="20" />
        История проверок
      </h3>
      <div class="history-actions">
        <button
          class="btn btn-secondary btn-small"
          type="button"
          @click="exportCsv"
        >
          <AppIcon name="download" :size="16" />
          Скачать CSV
        </button>
        <button class="btn btn-ghost btn-small" type="button" @click="confirmClear">
          <AppIcon name="trash" :size="16" />
          Очистить
        </button>
      </div>
    </div>

    <div class="table-scroll">
      <table class="history-table">
        <thead>
          <tr>
            <th>Время</th>
            <th>Кандидат</th>
            <th>Должность</th>
            <th>Вердикт</th>
            <th>Оценка</th>
            <th>Критичных</th>
            <th>Средних</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in entries" :key="entry.id">
            <td class="nowrap">{{ entry.createdAt }}</td>
            <td>{{ entry.candidate }}</td>
            <td>{{ entry.position }}</td>
            <td>
              <span
                class="badge"
                :class="`badge-${verdictClass(entry.verdict)}`"
              >
                {{ entry.verdictLabel }}
              </span>
            </td>
            <td>{{ entry.score !== null ? `${entry.score}%` : "—" }}</td>
            <td>{{ entry.high }}</td>
            <td>{{ entry.medium }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
