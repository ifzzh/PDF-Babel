<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
    <div class="relative w-full max-w-6xl h-[90vh] bg-white rounded-lg flex flex-col shadow-2xl overflow-hidden">
        
       <!-- Header -->
       <div class="flex items-center justify-between px-4 py-3 border-b bg-white z-10 shrink-0 relative h-16">
          <!-- Left: File Info -->
          <div class="flex items-center gap-3 overflow-hidden flex-1 min-w-0 mr-4">
             <!-- Icon -->
             <div class="p-1.5 rounded-md flex-shrink-0" :class="isGlossary ? 'bg-orange-100 text-orange-600' : 'bg-red-100 text-red-600'">
                <FileText v-if="!isGlossary" class="w-5 h-5" />
                <BookOpen v-else class="w-5 h-5" />
             </div>
             
             <div class="min-w-0">
                <h3 class="font-medium text-gray-900 truncate" :title="file?.filename || file?.name">{{ file?.filename || file?.name }}</h3>
                <p class="text-xs text-gray-500">{{ isGlossary ? 'Glossary Table' : 'PDF Preview' }}</p>
             </div>
          </div>
          
          <!-- Center: Fit Mode & Zoom Controls -->
          <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center gap-3">
             <!-- Fit Mode Toggle -->
             <button 
                @click="toggleFitMode"
                class="flex items-center gap-1 px-2 py-1.5 text-xs font-medium rounded border transition-colors bg-white hover:bg-gray-50 text-gray-700 w-24 justify-center flex-shrink-0"
                title="Toggle Fit Mode"
             >
                <svg v-if="fitMode === 'height'" class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" /></svg>
                <svg v-else class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                <span>{{ fitMode === 'height' ? 'Fit Height' : 'Fit Width' }}</span>
             </button>

             <!-- Zoom Controls -->
             <div class="flex items-center gap-1 border rounded-md p-0.5 bg-gray-50 flex-shrink-0">
                 <button @click="zoomOut" class="p-1 hover:bg-gray-200 rounded text-gray-600" title="Zoom Out">
                     <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" /></svg>
                 </button>
                 
                 <div class="relative flex items-center">
                     <input 
                        v-model.lazy="zoomInputValue"
                        @change="handleZoomInput"
                        type="text" 
                        class="w-10 text-center text-xs font-mono bg-transparent outline-none p-0"
                     >
                     <span class="text-[10px] text-gray-400 select-none">%</span>
                 </div>
                 
                 <button @click="zoomIn" class="p-1 hover:bg-gray-200 rounded text-gray-600" title="Zoom In">
                     <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                 </button>
             </div>
          </div>
          
          <!-- Right: Actions -->
          <div class="flex items-center gap-3 flex-1 justify-end">
             <!-- Maximize Button -->
             <router-link 
                v-if="jobId"
                :to="{ name: 'task-detail', params: { id: jobId }, query: { fileId: file?.file_id } }"
                class="p-2 hover:bg-gray-100 rounded-full text-gray-500 hover:text-blue-600 transition-colors"
                title="Open in Full Page"
                @click="$emit('close')"
             >
                <Maximize class="w-5 h-5" />
             </router-link>

             <!-- Download -->
             <a 
                v-if="url"
                :href="url" 
                :download="file?.filename || file?.name"
                class="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition-colors"
             >
                <DownloadCloud class="w-3.5 h-3.5" />
                Download
             </a>

             <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors">
                <X class="w-6 h-6" />
             </button>
          </div>
       </div>

       <!-- Content -->
       <div class="flex-1 overflow-hidden relative bg-gray-100 flex flex-col">
           <UnifiedPreview 
               :file="file"
               :url="url"
               :file-name="file?.filename || file?.name"
               v-model:scale="zoomLevel"
               v-model:fitMode="fitMode"
               @update:baseScale="(val) => baseScale = val"
           />
       </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { X, DownloadCloud, FileText, BookOpen, Maximize } from 'lucide-vue-next';
import UnifiedPreview from './UnifiedPreview.vue';


const props = defineProps<{
  file: any; // JobFile or File
  url: string;
  isOpen: boolean;
  jobId?: string;
}>();

const emit = defineEmits(['close']);

// Zoom State
const zoomLevel = ref(1.0);
const fitMode = ref<'width' | 'height' | 'manual'>('height');
const zoomInputValue = ref('100');
const baseScale = ref(1.0);

// Sync zoom input with level
watch([zoomLevel, baseScale], () => {
    const pct = baseScale.value > 0 ? (zoomLevel.value / baseScale.value) * 100 : zoomLevel.value * 100;
    zoomInputValue.value = Math.round(pct).toString();
});

const handleZoomInput = () => {
    const val = parseFloat(zoomInputValue.value);
    if (!isNaN(val)) {
        const targetScale = baseScale.value > 0 ? (val / 100) * baseScale.value : val / 100;
        zoomLevel.value = Math.min(Math.max(targetScale, 0.1), 5.0);
        if (fitMode.value !== 'manual') fitMode.value = 'manual';
    } else {
        const pct = baseScale.value > 0 ? (zoomLevel.value / baseScale.value) * 100 : zoomLevel.value * 100;
        zoomInputValue.value = Math.round(pct).toString();
    }
};

const zoomIn = () => {
    const step = 0.1 * (baseScale.value || 1.0);
    zoomLevel.value = Math.min(zoomLevel.value + step, 5.0);
    if (fitMode.value !== 'manual') fitMode.value = 'manual';
};

const zoomOut = () => {
    const step = 0.1 * (baseScale.value || 1.0);
    zoomLevel.value = Math.max(zoomLevel.value - step, 0.1);
    if (fitMode.value !== 'manual') fitMode.value = 'manual';
};

const toggleFitMode = () => {
    fitMode.value = fitMode.value === 'height' ? 'width' : 'height';
};

const isGlossary = computed(() => {
    if (!props.file) return false;
    // Check type property or filename extension
    if (props.file.type === 'glossary') return true;
    const name = props.file.filename || props.file.name || '';
    return name.toLowerCase().endsWith('.csv');
});
</script>
