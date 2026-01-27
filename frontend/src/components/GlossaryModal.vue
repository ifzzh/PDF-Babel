<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
    <div class="relative w-full max-w-4xl h-[80vh] bg-white rounded-lg flex flex-col shadow-2xl overflow-hidden">
        
       <!-- Header -->
       <div class="flex items-center justify-between px-4 py-3 border-b bg-white z-10 shrink-0">
          <div class="flex items-center gap-2 overflow-hidden">
             <div class="p-1.5 bg-yellow-100 text-yellow-700 rounded-md">
                <BookOpen class="w-5 h-5" />
             </div>
             <div class="min-w-0">
                <h3 class="font-medium text-gray-900 truncate">{{ file?.filename }}</h3>
                <p class="text-xs text-gray-500">Glossary CSV</p>
             </div>
          </div>
          
          <div class="flex items-center gap-3">
             <a 
                v-if="file"
                :href="file.url" 
                download
                class="button-text text-sm"
             >
                Download CSV
             </a>
             <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors">
                <X class="w-6 h-6" />
             </button>
          </div>
       </div>

       <!-- Content -->
       <div class="flex-1 overflow-hidden">
           <GlossaryTable :file="file" />
       </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { X, BookOpen } from 'lucide-vue-next';
import GlossaryTable from './GlossaryTable.vue';
import type { JobFile } from '../types';

const props = defineProps<{
  file: JobFile | null;
  isOpen: boolean;
}>();

const emit = defineEmits(['close']);

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) emit('close');
};

onMounted(() => window.addEventListener('keydown', handleKeydown));
onUnmounted(() => window.removeEventListener('keydown', handleKeydown));
</script>

<style scoped>
.button-text {
    @apply text-blue-600 hover:text-blue-700 font-medium hover:underline transition-colors;
}
</style>
