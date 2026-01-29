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
        <div v-if="filteredResultFiles && filteredResultFiles.length > 0">
          <h4 class="px-2 mb-2 text-xs font-medium text-gray-500 uppercase">Results</h4>
          <div class="space-y-1">
            <button 
              v-for="file in filteredResultFiles" 
              :key="file.file_id"
              @click="selectFile({ type: 'result', file: file })"
              class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors"
              :class="isActive('result', file.file_id) ? 'bg-purple-100 text-purple-700' : 'hover:bg-gray-100 text-gray-700'"
            >
              <div class="flex items-center gap-2">
                <span class="p-1.5 rounded-md bg-white border border-gray-200" :class="file.type === 'glossary' ? 'text-orange-500' : 'text-purple-500'">
                  <!-- Icon based on type -->
                  <svg v-if="file.type === 'glossary'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

      <!-- Bottom Progress (Circular) -->
      <div class="h-64 shrink-0 p-4 border-t bg-white flex flex-col items-center justify-start pt-8">
         <CircularStageProgress
            :stages="job.stages"
            :current-stage-name="job.stageName"
            :current-stage-progress="job.stageProgress"
            :overall-progress="job.overallProgress"
            :status="job.status"
            :size="140"
            :stroke-width="10"
         />
      </div>
    </div>

    <!-- Main Preview Area -->
    <div class="flex-1 flex flex-col bg-gray-200 relative overflow-hidden">
      <!-- Top Bar -->
      <div v-if="activeItem" class="bg-white border-b px-4 py-2 flex items-center justify-between shadow-sm z-10 space-x-4">
         <!-- Left: Filename -->
         <h3 class="font-medium text-sm text-gray-700 truncate min-w-0 flex-1">{{ activeItem.file.name || activeItem.file.filename }}</h3>
         
         <!-- Center: Zoom Controls -->
         <div class="flex items-center gap-1 border rounded-md p-0.5 bg-gray-50 flex-shrink-0">
             <button @click="zoomOut" class="p-1 hover:bg-gray-200 rounded text-gray-600" title="Zoom Out">
                 <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" /></svg>
             </button>
             
             <div class="relative flex items-center">
                 <input 
                    v-model.lazy="zoomInputValue"
                    @change="handleZoomInput"
                    type="text" 
                    class="w-8 text-center text-xs font-mono bg-transparent outline-none p-0"
                 >
                 <span class="text-[10px] text-gray-400 select-none">%</span>
             </div>
             
             <button @click="zoomIn" class="p-1 hover:bg-gray-200 rounded text-gray-600" title="Zoom In">
                 <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
             </button>
         </div>

         <!-- Right: Actions -->
         <div class="flex items-center gap-2 flex-shrink-0">
             <!-- Fit Mode Toggle -->
             <button 
                @click="toggleFitMode"
                class="flex items-center gap-1 px-2 py-1.5 text-xs font-medium rounded border transition-colors bg-white hover:bg-gray-50 text-gray-700 w-24 justify-center"
                title="Toggle Fit Mode"
             >
                <svg v-if="fitMode === 'height'" class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" /></svg>
                <svg v-else class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                <span>{{ fitMode === 'height' ? 'Fit Height' : 'Fit Width' }}</span>
             </button>

             <!-- Maximize Button -->
             <button 
                @click="goToHistory"
                class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                title="View Full Detail"
             >
                <Maximize class="w-4 h-4" />
             </button>

             <a 
               :href="activeUrl" 
               :download="activeItem.file.name || activeItem.file.filename"
               class="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition-colors"
             >
               <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
               Download
             </a>
         </div>
      </div>

      <!-- Preview Content -->
      <div class="flex-1 relative w-full h-full border-t border-gray-200">
          <UnifiedPreview 
             v-if="activeItem"
             :file="activeItem.file" 
             :url="activeUrl || undefined"
             :file-name="activeItem.file.name || activeItem.file.filename"
             v-model:scale="zoomLevel"
             v-model:fitMode="fitMode"
             @update:baseScale="(val) => baseScale = val"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-400 bg-gray-50">
             Select a file to preview
          </div>
      </div>
    </div>
  </div>

  <!-- Fullscreen Modal -->
  <PreviewModal 
     :is-open="isModalOpen"
     :file="activeItem?.file"
     :url="activeUrl || ''"
     @close="isModalOpen = false"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { Maximize } from 'lucide-vue-next';
import type { JobFile } from '../types';
import CircularStageProgress from './CircularStageProgress.vue';

import PreviewModal from './PreviewModal.vue';
import UnifiedPreview from './UnifiedPreview.vue';

const props = defineProps<{
  sourceFile: File | null;
  resultFiles: JobFile[];
  job: any; // Using any for simplicity as Job type might need update or mapped from useJob
}>();

const router = useRouter();

// State for local object URLs to revoke them later
const objectUrls = new Set<string>();

interface ActiveItem {
  type: 'source' | 'result';
  file: any;
}

const isModalOpen = ref(false);
const activeItem = ref<ActiveItem | null>(null);

const goToHistory = () => {
    if (props.job && props.job.id) {
        router.push({ name: 'task-detail', params: { id: props.job.id } });
    }
};

// Zoom State
const zoomLevel = ref(1.0);
const fitMode = ref<'width' | 'height' | 'manual'>('height');
const zoomInputValue = ref('100');
const baseScale = ref(1.0); // The scale factor corresponding to "100%" (Fit Height)

// Sync zoom input with level
watch([zoomLevel, baseScale], () => {
    // Displayed % = (Absolute Scale / Base Scale) * 100
    const pct = (zoomLevel.value / baseScale.value) * 100;
    zoomInputValue.value = Math.round(pct).toString();
});

const handleZoomInput = () => {
    const val = parseFloat(zoomInputValue.value);
    if (!isNaN(val)) {
        // Absolute Scale = (Display % / 100) * Base Scale
        const targetScale = (val / 100) * baseScale.value;
        zoomLevel.value = Math.min(Math.max(targetScale, 0.1), 5.0);
        if (fitMode.value !== 'manual') fitMode.value = 'manual';
    } else {
        const pct = (zoomLevel.value / baseScale.value) * 100;
        zoomInputValue.value = Math.round(pct).toString();
    }
};

const zoomIn = () => {
    // Increase by 10% of the base scale
    const step = 0.1 * baseScale.value;
    zoomLevel.value = Math.min(zoomLevel.value + step, 5.0);
    if (fitMode.value !== 'manual') fitMode.value = 'manual';
};

const zoomOut = () => {
    const step = 0.1 * baseScale.value;
    zoomLevel.value = Math.max(zoomLevel.value - step, 0.1);
    if (fitMode.value !== 'manual') fitMode.value = 'manual';
};

const toggleFitMode = () => {
    fitMode.value = fitMode.value === 'height' ? 'width' : 'height';
};

const filteredResultFiles = computed(() => {
  if (!props.resultFiles) return [];
  // Exclude 'original' type files from the results list as they are shown in Source section
  return props.resultFiles.filter(f => f.type !== 'original');
});

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
