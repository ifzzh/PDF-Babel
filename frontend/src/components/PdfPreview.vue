<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
    <div class="relative w-full max-w-6xl h-[90vh] bg-gray-100 rounded-lg flex flex-col overflow-hidden">
      <!-- Toolbar -->
      <div class="bg-white px-4 py-2 border-b flex items-center justify-between shadow-sm z-10">
        <h3 class="font-medium text-gray-700 truncate pr-4">{{ file?.filename }}</h3>
        
        <div class="flex items-center space-x-4">
           <!-- Maximize Button -->
           <router-link 
              v-if="jobId && file"
              :to="{ name: 'task-detail', params: { id: jobId }, query: { fileId: file.file_id } }"
              class="p-2 hover:bg-gray-100 rounded text-gray-500 hover:text-blue-600 transition-colors"
              title="Open in Full Page"
           >
              <Maximize class="w-5 h-5" />
           </router-link>

           <!-- Download Button -->
           <a 
              v-if="file"
              :href="file.url" 
              download
              class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded border border-blue-200 transition-colors flex items-center gap-1"
           >
              <DownloadCloud class="w-3.5 h-3.5" />
              Download
           </a>

           <button @click="$emit('close')" class="p-2 hover:bg-red-50 text-gray-500 hover:text-red-500 rounded-full transition-colors">
             <X class="w-6 h-6" />
           </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 bg-gray-200 overflow-hidden relative flex flex-col items-center justify-center">
         <div v-if="file" class="w-full h-full">
            <iframe 
                v-if="isPreviewable(file)"
                :src="file.url + '#toolbar=0'"
                class="w-full h-full border-none"
            ></iframe>
            <div v-else class="flex flex-col items-center justify-center h-full text-gray-500">
                <p class="mb-2">Preview not available for this file type.</p>
                <a :href="file.url" download class="text-blue-600 underline text-sm">Download to view</a>
            </div>
         </div>
         <div v-else class="text-gray-400">
            No file selected
         </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { X, DownloadCloud, Maximize } from 'lucide-vue-next';
import type { JobFile } from '../types';

const props = defineProps<{
  file: JobFile | null;
  isOpen: boolean;
  jobId?: string;
}>();

const emit = defineEmits(['close']);

const isPreviewable = (file: JobFile) => {
    return file.filename.toLowerCase().endsWith('.pdf') || 
           file.url?.toLowerCase().endsWith('.pdf');
};

// Close on Escape
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) emit('close');
};

onMounted(() => window.addEventListener('keydown', handleKeydown));
onUnmounted(() => window.removeEventListener('keydown', handleKeydown));
</script>
