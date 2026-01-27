<template>
  <div class="bg-white rounded-lg shadow p-4 border border-gray-100">
    <div class="flex items-center justify-between mb-2">
      <span class="font-medium text-gray-800">{{ stageName }}</span>
      <span class="text-sm font-bold text-blue-600">{{ overallProgress.toFixed(1) }}%</span>
    </div>
    
    <!-- Overall Progress -->
    <div class="w-full bg-gray-200 rounded-full h-2.5 mb-4">
      <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-300" :style="{ width: overallProgress + '%' }"></div>
    </div>

    <!-- Stage Progress -->
    <div v-if="stageProgress > 0 && status === 'running'" class="text-xs text-gray-500 mb-1">
      Current Stage: {{ stageProgress.toFixed(1) }}%
    </div>
    <div v-if="stageProgress > 0 && status === 'running'" class="w-full bg-gray-100 rounded-full h-1.5">
      <div class="bg-blue-400 h-1.5 rounded-full transition-all duration-300" :style="{ width: stageProgress + '%' }"></div>
    </div>

    <!-- Status Messages -->
    <div v-if="error" class="mt-3 p-3 bg-red-50 text-red-700 rounded text-sm border border-red-200">
      <strong>Error:</strong> {{ error }}
    </div>
    <div v-if="info" class="mt-2 text-sm text-gray-500">
      {{ info }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  overallProgress: number;
  stageProgress: number;
  stageName: string;
  status: string;
  error?: string;
  info?: string;
}>();
</script>
