<template>
  <div class="relative group inline-flex items-center cursor-help isolate">
    <Info class="w-3.5 h-3.5 text-gray-400 hover:text-gray-600 transition-colors" />
    <div 
      class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1.5 text-xs text-white bg-gray-800 rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none z-[100] w-max max-w-[200px] text-center normal-case font-normal leading-relaxed"
    >
      {{ text }}
      <!-- Arrow -->
      <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Info } from 'lucide-vue-next';

defineProps<{
  text: string
}>();
</script>
