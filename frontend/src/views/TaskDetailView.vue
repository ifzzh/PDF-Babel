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
                                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                <div class="bg-white border-b px-4 py-2 flex items-center justify-between shadow-sm z-10">
                    <div class="text-sm font-medium text-gray-700 truncate max-w-md">{{ previewFile.filename }}</div>
                    <div class="flex items-center gap-2">
                        <a 
                            :href="previewFile.url" 
                            :download="previewFile.filename"
                            class="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded border border-blue-200 transition-colors flex items-center gap-1"
                        >
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Download
                        </a>
                    </div>
                </div>
                
                <!-- PDF Viewer (iframe) -->
                <div class="flex-1 bg-gray-200 overflow-hidden relative">
                     <iframe 
                        v-if="isPreviewable(previewFile)"
                        :src="previewFile.url + '#toolbar=0'"
                        class="w-full h-full border-none"
                    ></iframe>
                    <div v-else class="flex-1 flex flex-col items-center justify-center h-full text-gray-500">
                        <p class="mb-2">Preview not available for this file type.</p>
                        <a :href="previewFile.url" download class="text-blue-600 underline text-sm">Download to view</a>
                    </div>
                </div>
            </div>
        </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { fetchJob, fetchJobFiles } from '../api';
import type { Job, JobFile } from '../types';

const route = useRoute();
const jobId = route.params.id as string;

const loading = ref(true);
const job = ref<Job | null>(null);
const files = ref<JobFile[]>([]);
const previewFile = ref<JobFile | null>(null);

const jobName = computed(() => {
    if (!job.value) return 'Loading...';
    return job.value.display_name || job.value.original_filename || job.value.folder_name || 'Untitled';
});

const jobStatus = computed(() => job.value?.status);

// Split files into Source (uploaded) vs Results (mono/dual/etc)
const sourceFiles = computed(() => {
    return files.value.filter(f => f.type === 'source' || f.type === 'original'); // Assuming 'source' or inferred
});

// Since API might not explicitly label "source", we might need logic. 
// Usually 'uploaded' file is not in result list unless we specifically fetch it or if backend includes it.
// Based on ResultList, it seems `fetchJobFiles` returns generated files.
// Does it return the source file? Backend contract says:
// GET /api/jobs/{id}/files -> returns list of files in the folder?
// If it returns all, we can distinguish by type or name.
// Let's assume for now everything is in the list and we group by logic:
// Mono/Dual are results. Original is source.

const resultFiles = computed(() => {
    return files.value.filter(f => ['mono', 'dual', 'result'].includes(f.type) || (f.type !== 'source' && f.type !== 'original'));
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
            previewFile.value = resultFiles.value[0];
        } else if (files.value.length > 0) {
            previewFile.value = files.value[0];
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

const isPreviewable = (file: JobFile) => {
    return file.filename.toLowerCase().endsWith('.pdf') || 
           file.url?.toLowerCase().endsWith('.pdf');
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
