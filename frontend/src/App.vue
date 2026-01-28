<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans">
    <header class="bg-white border-b border-gray-200">
      <div class="w-full px-6 h-16 flex items-center justify-between">
        <router-link to="/" class="flex items-center space-x-2">
           <svg class="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
           </svg>
           <span class="font-bold text-xl tracking-tight">PDF Babel</span>
        </router-link>
        
        <div class="flex items-center space-x-6">
           <nav class="flex items-center space-x-4">
              <router-link 
                to="/" 
                class="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
                active-class="text-blue-600 font-semibold"
              >
                Translator
              </router-link>
              <router-link 
                to="/history" 
                class="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
                active-class="text-blue-600 font-semibold"
              >
                History
              </router-link>
              <router-link 
                to="/queue" 
                class="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
                active-class="text-blue-600 font-semibold"
              >
                Queue
              </router-link>
           </nav>
           <div class="text-xs text-gray-400 bg-gray-50 px-2 py-1 rounded">v0.1</div>
        </div>
      </div>
    </header>
    
    <main>
      <router-view></router-view>
    </main>

    <QueueRail />
  </div>
</template>

<script setup lang="ts">
import QueueRail from './components/QueueRail.vue';
</script>
