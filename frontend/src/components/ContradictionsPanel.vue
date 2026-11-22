<script setup lang="ts">
import { computed } from "vue";

import type { Contradictions } from "../types";
import { severityClass, severityLabel } from "../utils/format";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ contradictions: Contradictions }>();

const counts = computed(
  () => props.contradictions.counts ?? { high: 0, medium: 0, low: 0 },
);
const items = computed(() => props.contradictions.items ?? []);

function sourceLabel(source?: string): string {
  return source === "llm" ? "LLM" : "правило";
}
</script>

<template>
  <section class="section">
    <div class="section-header">
      <h3 class="section-title">
        <span class="section-index">1</span>
        Внутренние противоречия
      </h3>
    </div>

    <div class="counts-grid">
      <div class="count-card count-high">
        <span class="count-value">{{ counts.high ?? 0 }}</span>
        <span class="count-label">
          <span class="count-dot count-dot-high"></span>
          Критичные
        </span>
      </div>
      <div class="count-card count-medium">
        <span class="count-value">{{ counts.medium ?? 0 }}</span>
        <span class="count-label">
          <span class="count-dot count-dot-medium"></span>
          Средние
        </span>
      </div>
      <div class="count-card count-low">
        <span class="count-value">{{ counts.low ?? 0 }}</span>
        <span class="count-label">
          <span class="count-dot count-dot-low"></span>
          Незначительные
        </span>
      </div>
    </div>

    <p v-if="contradictions.summary" class="info-box">
      {{ contradictions.summary }}
    </p>

    <div v-if="!items.length" class="empty-state empty-success">
      <AppIcon class="empty-icon" name="check" :size="20" />
      <p>Формальных и смысловых противоречий не найдено.</p>
    </div>

    <div v-else class="findings">
      <article
        v-for="(item, index) in items"
        :key="item.code ? `${item.code}-${index}` : index"
        class="finding"
      >
        <div class="finding-head">
          <span class="badge" :class="`badge-${severityClass(item.severity)}`">
            {{ severityLabel(item.severity) }}
          </span>
          <h4 class="finding-title">{{ item.title || "Противоречие" }}</h4>
          <span
            class="finding-source"
            :class="{ 'is-llm': item.source === 'llm' }"
          >
            {{ sourceLabel(item.source) }}
          </span>
        </div>

        <p v-if="item.description" class="finding-desc">
          {{ item.description }}
        </p>

        <div v-if="item.fields?.length || item.code" class="finding-foot">
          <div v-if="item.fields?.length" class="chips">
            <span v-for="field in item.fields" :key="field" class="chip">
              {{ field }}
            </span>
          </div>
          <code v-if="item.code" class="finding-code">{{ item.code }}</code>
        </div>
      </article>
    </div>
  </section>
</template>
