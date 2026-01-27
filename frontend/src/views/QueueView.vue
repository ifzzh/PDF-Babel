<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    <div class="flex items-center justify-between">
       <div class="flex items-center space-x-4">
          <router-link to="/" class="p-2 hover:bg-gray-100 rounded-full text-gray-600 transition-colors">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </router-link>
          <h1 class="text-2xl font-bold text-gray-900">Task Queue</h1>
       </div>
    </div>

    <div class="bg-white rounded-lg shadow">
       <div class="border-b p-4">
         <h2 class="font-medium text-lg">Active Queue</h2>
         <p class="text-xs text-gray-500 mt-1">Manage running and queued tasks</p>
       </div>
       <div class="p-4">
          <QueuePanel />
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import QueuePanel from '../components/QueuePanel.vue';
</script>
