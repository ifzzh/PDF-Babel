<template>
  <div class="flex h-full overflow-hidden bg-white">
    <!-- Left Sidebar: File List -->
    <div class="w-64 flex-shrink-0 border-r bg-gray-50 flex flex-col">
      <div class="p-4 border-b">
        <h3 class="font-semibold text-gray-700 uppercase text-xs tracking-wider">Files</h3>
      </div>
      
      <div class="flex-1 overflow-y-auto p-3 space-y-6">
        <!-- Source Files -->
        <div v-if="sourceFile">
          <h4 class="px-2 mb-2 text-xs font-medium text-gray-500 uppercase">Source</h4>
          <button 
            @click="selectFile({ type: 'source', file: sourceFile })"
            class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors group"
            :class="isActive('source') ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100 text-gray-700'"
          >
            <div class="flex items-center gap-2">
              <span class="p-1.5 rounded-md bg-white border border-gray-200 text-gray-500">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </span>
              <div class="min-w-0">
                <p class="font-medium truncate">{{ sourceFile.name }}</p>
                <p class="text-xs text-gray-400">{{ formatSize(sourceFile.size) }}</p>
              </div>
            </div>
          </button>
        </div>

        <!-- Result Files -->
        <div v-if="resultFiles && resultFiles.length > 0">
          <h4 class="px-2 mb-2 text-xs font-medium text-gray-500 uppercase">Results</h4>
          <div class="space-y-1">
            <button 
              v-for="file in resultFiles" 
              :key="file.file_id"
              @click="selectFile({ type: 'result', file: file })"
              class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors"
              :class="isActive('result', file.file_id) ? 'bg-purple-100 text-purple-700' : 'hover:bg-gray-100 text-gray-700'"
            >
              <div class="flex items-center gap-2">
                <span class="p-1.5 rounded-md bg-white border border-gray-200" :class="file.file_type === 'glossary' ? 'text-orange-500' : 'text-purple-500'">
                  <!-- Icon based on type -->
                  <svg v-if="file.file_type === 'glossary'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </span>
                <div class="min-w-0">
                  <p class="font-medium truncate">{{ file.filename }}</p>
                  <p class="text-xs opacity-70">{{ formatSize(file.size) }}</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Preview Area -->
    <div class="flex-1 flex flex-col bg-gray-200 relative overflow-hidden">
      <!-- Top Bar -->
      <div v-if="activeItem" class="bg-white border-b px-4 py-2 flex items-center justify-between shadow-sm z-10">
         <h3 class="font-medium text-sm text-gray-700">{{ activeItem.file.name || activeItem.file.filename }}</h3>
         <a 
           :href="activeUrl" 
           :download="activeItem.file.name || activeItem.file.filename"
           class="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition-colors"
         >
           <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
           Download
         </a>
      </div>

      <!-- Preview Content -->
      <div class="flex-1 relative w-full h-full">
         <iframe 
           v-if="activeUrl && isPdf"
           :src="activeUrl + '#toolbar=0'"
           class="w-full h-full border-none"
         ></iframe>
         
         <div v-else-if="activeUrl" class="w-full h-full flex flex-col items-center justify-center text-gray-500 bg-gray-50">
            <p class="mb-2">Preview not available for this file type.</p>
            <a :href="activeUrl" download class="text-blue-600 hover:underline text-sm">Download to view</a>
         </div>

         <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
            Select a file to preview
         </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import type { JobFile } from '../types';

const props = defineProps<{
  sourceFile: File | null;
  resultFiles: JobFile[];
}>();

// State for local object URLs to revoke them later
const objectUrls = new Set<string>();

interface ActiveItem {
  type: 'source' | 'result';
  file: any;
}

const activeItem = ref<ActiveItem | null>(null);

const activeUrl = computed(() => {
  if (!activeItem.value) return null;
  
  if (activeItem.value.type === 'source') {
    // For source file (File object), create Object URL
    // Ideally we should cache this
    const url = URL.createObjectURL(activeItem.value.file);
    objectUrls.add(url);
    return url;
  } else {
    // For result files (JobFile), use .url
    return activeItem.value.file.url;
  }
});

const isPdf = computed(() => {
  if (!activeItem.value) return false;
  const name = activeItem.value.file.name || activeItem.value.file.filename;
  return name.toLowerCase().endsWith('.pdf');
});

const selectFile = (item: ActiveItem) => {
  activeItem.value = item;
};

const isActive = (type: string, id?: string) => {
   if (!activeItem.value) return false;
   if (activeItem.value.type !== type) return false;
   if (type === 'result') {
     return activeItem.value.file.file_id === id;
   }
   return true;
};

const formatSize = (bytes?: number) => {
  if (bytes === undefined) return '';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Auto-select source file when uploaded
watch(() => props.sourceFile, (newFile) => {
  if (newFile) {
    selectFile({ type: 'source', file: newFile });
  } else {
    activeItem.value = null;
  }
}, { immediate: true });

// Cleanup URLs
onUnmounted(() => {
  objectUrls.forEach(url => URL.revokeObjectURL(url));
  objectUrls.clear();
});
</script>
