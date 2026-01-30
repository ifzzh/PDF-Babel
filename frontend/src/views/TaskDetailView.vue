<template>
  <div class="h-[calc(100vh-64px)] flex flex-col bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b px-6 py-4 flex items-center shadow-sm z-10">
       <router-link to="/history" class="mr-4 p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
       </router-link>
       <div>
          <h1 class="text-xl font-bold text-gray-800 flex items-center gap-2">
             {{ jobName }}
             <span v-if="jobStatus" 
                class="text-xs px-2 py-0.5 rounded capitalize font-normal border"
                :class="{
                    'bg-green-100 text-green-700 border-green-200': jobStatus === 'finished',
                    'bg-yellow-100 text-yellow-700 border-yellow-200': jobStatus === 'queued',
                    'bg-blue-100 text-blue-700 border-blue-200': jobStatus === 'running',
                    'bg-red-100 text-red-700 border-red-200': jobStatus === 'failed',
                    'bg-gray-100 text-gray-600 border-gray-200': jobStatus === 'canceled'
                }"
             >
                {{ jobStatus }}
             </span>
          </h1>
          <p class="text-xs text-gray-500 mt-0.5 font-mono">{{ jobId }}</p>
       </div>
    </header>
    
    <div class="flex-1 flex overflow-hidden">
        <!-- Sidebar: File List -->
        <aside class="w-1/3 min-w-[300px] max-w-md bg-white border-r flex flex-col">
            <div class="p-4 border-b bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Files
            </div>
            
            <div v-if="loading" class="p-8 text-center text-gray-500">
                Loading details...
            </div>
            
            <div v-else class="flex-1 overflow-y-auto p-4 space-y-6">
                 <!-- Source Files -->
                 <div v-if="sourceFiles.length">
                     <h3 class="text-xs font-bold text-gray-400 mb-2 px-1">Source</h3>
                     <div class="space-y-2">
                         <div v-for="file in sourceFiles" :key="file.file_id" 
                            class="group p-3 rounded-lg border hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-all"
                            :class="{'ring-2 ring-blue-500 bg-blue-50': previewFile?.file_id === file.file_id}"
                            @click="selectFile(file)"
                         >
                            <div class="flex items-center gap-3">
                                <div class="p-2 bg-gray-100 rounded text-gray-500">
                                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                </div>
                                <div class="min-w-0">
                                    <div class="text-sm font-medium text-gray-700 truncate group-hover:text-blue-700">{{ file.filename }}</div>
                                    <div class="text-xs text-gray-400">{{ formatSize(file.size) }}</div>
                                </div>
                            </div>
                         </div>
                     </div>
                 </div>

                 <!-- Results -->
                 <div v-if="resultFiles.length">
                     <h3 class="text-xs font-bold text-gray-400 mb-2 px-1">Results</h3>
                     <div class="space-y-2">
                         <div v-for="file in resultFiles" :key="file.file_id" 
                            class="group p-3 rounded-lg border hover:border-purple-300 hover:bg-purple-50 cursor-pointer transition-all"
                            :class="{'ring-2 ring-purple-500 bg-purple-50': previewFile?.file_id === file.file_id}"
                            @click="selectFile(file)"
                         >
                            <div class="flex items-center gap-3">
                                <div class="p-2 bg-purple-100 rounded text-purple-600">
                                    <BookOpen v-if="file.type === 'glossary'" class="w-5 h-5 text-amber-600" />
                                    <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                </div>
                                <div class="min-w-0">
                                    <div class="text-sm font-medium text-gray-700 truncate group-hover:text-purple-700">
                                        {{ file.filename }}
                                    </div>
                                    <div class="text-xs text-gray-400 flex items-center gap-1">
                                        <span class="capitalize bg-gray-100 px-1 rounded">{{ file.type }}</span>
                                        <span>{{ formatSize(file.size) }}</span>
                                    </div>
                                </div>
                            </div>
                         </div>
                     </div>
                 </div>
            </div>
        </aside>

        <!-- Main Area: Preview -->
        <main class="flex-1 bg-gray-100 relative flex flex-col">
            <div v-if="!previewFile" class="flex-1 flex flex-col items-center justify-center text-gray-400 p-8">
                <svg class="w-16 h-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>Select a file to preview</p>
            </div>
            
            <div v-else class="flex-1 flex flex-col h-full">
                <!-- Toolbar -->
                <div class="bg-white border-b px-4 py-2 flex items-center justify-between shadow-sm z-10 space-x-4">
                    <div class="text-sm font-medium text-gray-700 truncate max-w-md">{{ previewFile.filename }}</div>
                    <div class="flex items-center gap-2">
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
                                   class="w-8 text-center text-xs font-mono bg-transparent outline-none p-0"
                                >
                                <span class="text-[10px] text-gray-400 select-none">%</span>
                            </div>
                            <button @click="zoomIn" class="p-1 hover:bg-gray-200 rounded text-gray-600" title="Zoom In">
                                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                            </button>
                        </div>

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

                        <a 
                            :href="previewFile.url" 
                            download
                            class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded border border-blue-200 transition-colors flex items-center gap-1"
                        >
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Download
                        </a>
                    </div>
                </div>
                
                <!-- Preview -->
                <div class="flex-1 bg-gray-200 overflow-hidden relative flex flex-col">
                     <UnifiedPreview 
                        v-if="previewFile"
                        :file="previewFile"
                        :url="previewFile.url"
                        :file-name="previewFile.filename"
                        v-model:scale="zoomLevel"
                        v-model:fitMode="fitMode"
                        @update:baseScale="(val) => baseScale = val"
                     />
                </div>
            </div>
        </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { fetchJob, fetchJobFiles } from '../api';
import { BookOpen } from 'lucide-vue-next';
import UnifiedPreview from '../components/UnifiedPreview.vue';
import type { Job, JobFile } from '../types';

const route = useRoute();
const jobId = route.params.id as string;

const loading = ref(true);
const job = ref<Job | null>(null);
const files = ref<JobFile[]>([]);
const previewFile = ref<JobFile | null>(null);

// Zoom state (match Home preview behavior)
const zoomLevel = ref(1.0);
const fitMode = ref<'width' | 'height' | 'manual'>('height');
const zoomInputValue = ref('100');
const baseScale = ref(1.0);

watch([zoomLevel, baseScale], () => {
    const pct = (zoomLevel.value / baseScale.value) * 100;
    zoomInputValue.value = Math.round(pct).toString();
});

const handleZoomInput = () => {
    const val = parseFloat(zoomInputValue.value);
    if (!isNaN(val)) {
        const targetScale = (val / 100) * baseScale.value;
        zoomLevel.value = Math.min(Math.max(targetScale, 0.1), 5.0);
        if (fitMode.value !== 'manual') fitMode.value = 'manual';
    } else {
        const pct = (zoomLevel.value / baseScale.value) * 100;
        zoomInputValue.value = Math.round(pct).toString();
    }
};

const zoomIn = () => {
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

const jobName = computed(() => {
    if (!job.value) return 'Loading...';
    return job.value.display_name || job.value.original_filename || job.value.folder_name || 'Untitled';
});

const jobStatus = computed(() => job.value?.status);

// Split files into Source (uploaded) vs Results (mono/dual/etc)
const sourceFiles = computed(() => {
    return files.value.filter(f => f.type === 'source' || f.type === 'original'); 
});

const resultFiles = computed(() => {
    return files.value.filter(f => ['mono', 'dual', 'result', 'glossary'].includes(f.type) || (f.type !== 'source' && f.type !== 'original'));
});

// Refine logic:
// If backend returns `type` field correctly:
//   source/original -> Source
//   mono/dual/translation -> Results
// If backend just lists files:
//   check filename patterns or ensure backend sets type.

const loadData = async () => {
    loading.value = true;
    try {
        const [j, f] = await Promise.all([
            fetchJob(jobId),
            fetchJobFiles(jobId)
        ]);
        job.value = j.data;
        files.value = f.data;
        
        // Auto-select file based on query param or default logic
        const queryFileId = route.query.fileId as string;
        if (queryFileId) {
            const found = files.value.find(f => f.file_id === queryFileId);
            if (found) {
                previewFile.value = found;
                return;
            }
        }

        // Default fallback
        if (resultFiles.value.length > 0) {
            previewFile.value = resultFiles.value[0] ?? null;
        } else if (files.value.length > 0) {
            previewFile.value = files.value[0] ?? null;
        }
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const selectFile = (file: JobFile) => {
    previewFile.value = file;
};

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

onMounted(loadData);
</script>
