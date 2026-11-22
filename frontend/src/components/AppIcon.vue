<script setup lang="ts">
type IconName =
  | "receipt"
  | "refresh"
  | "chart"
  | "download"
  | "trash"
  | "paperclip"
  | "file"
  | "search"
  | "bulb"
  | "check"
  | "warning"
  | "x"
  | "target";

withDefaults(
  defineProps<{
    name: IconName;
    size?: number | string;
    strokeWidth?: number;
  }>(),
  {
    size: 18,
    strokeWidth: 1.8,
  },
);

const ICON_PATHS: Record<IconName, string[]> = {
  receipt: [
    "M6 3h12a1 1 0 0 1 1 1v17l-3-2-3 2-3-2-3 2V4a1 1 0 0 1 1-1Z",
    "M9 7h6",
    "M9 11h6",
    "M9 15h4",
  ],
  refresh: ["M21 12a9 9 0 1 1-2.6-6.4", "M21 3v6h-6"],
  chart: ["M4 20V10", "M10 20V4", "M16 20v-7", "M2 20h20"],
  download: ["M12 3v12", "m7 10 5 5 5-5", "M5 21h14"],
  trash: [
    "M4 7h16",
    "M9 7V4h6v3",
    "m6 7 1 13h10l1-13",
    "M10 11v5",
    "M14 11v5",
  ],
  paperclip: [
    "m21 11-9 9a5.5 5.5 0 0 1-7.8-7.8l9-9a3.7 3.7 0 0 1 5.2 5.2l-9 9a1.8 1.8 0 0 1-2.6-2.6l8.3-8.3",
  ],
  file: [
    "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z",
    "M14 3v5h5",
  ],
  search: ["M18 11a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z", "m20 20-3.5-3.5"],
  bulb: [
    "M9 18h6",
    "M10 21h4",
    "M12 3a6 6 0 0 0-3.6 10.8c.5.4.8 1 .9 1.6l.1.6h5.2l.1-.6c.1-.6.4-1.2.9-1.6A6 6 0 0 0 12 3Z",
  ],
  check: ["m4 12 5 5L20 6"],
  warning: ["M12 3 2 21h20L12 3Z", "M12 9v5", "M12 18h.01"],
  x: ["M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z", "m9 9 6 6", "m15 9-6 6"],
  target: [
    "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    "M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0Z",
    "M13 12a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z",
  ],
};
</script>

<template>
  <svg
    class="icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="path in ICON_PATHS[name]" :key="path" :d="path" />
  </svg>
</template>
