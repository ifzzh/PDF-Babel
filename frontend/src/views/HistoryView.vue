<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    <div class="flex items-center justify-between">
       <div class="flex items-center space-x-4">
          <router-link to="/" class="p-2 hover:bg-gray-100 rounded-full text-gray-600 transition-colors">
            <ArrowLeft class="w-6 h-6" />
          </router-link>
          <h1 class="text-2xl font-bold text-gray-900">Task History & Queue</h1>
       </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
       <!-- Queue Manager -->
       <div class="lg:col-span-1">
          <section class="bg-white rounded-lg shadow lg:sticky lg:top-8">
             <div class="border-b p-4">
               <h2 class="font-medium text-lg">Active Queue</h2>
               <p class="text-xs text-gray-500 mt-1">Manage running and queued tasks</p>
             </div>
             <div class="p-4">
                <QueuePanel @refresh="refreshHistory" />
             </div>
          </section>
       </div>
       
       <!-- History List -->
       <div class="lg:col-span-2">
          <section class="bg-white rounded-lg shadow">
             <div class="border-b p-4 flex justify-between items-center">
               <h2 class="font-medium text-lg">Task History</h2>
               <button @click="refreshHistory" class="text-sm text-blue-600 hover:text-blue-700">Refresh</button>
             </div>
             <div class="p-4">
               <HistoryList ref="historyRef" @select="viewDetails" />
             </div>
          </section>
       </div>
    </div>

    <!-- Detail Modal (Reuse ResultList + Preview?) -->
    <!-- For MVP, maybe just jump to Home? Or simple modal -->
    <!-- Contract says: "点击条目进入详情或加载 files 列表与预览" -->
    <!-- Let's do a simple modal to show files for the selected history item -->
    
    <div v-if="selectedJobId" class="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4">
       <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
          <div class="p-4 border-b flex justify-between items-center">
             <h3 class="font-medium">Job Results</h3>
             <button @click="selectedJobId = ''"><X class="w-6 h-6 text-gray-400 hover:text-gray-600"/></button>
          </div>
          <div class="p-6 overflow-y-auto">
             <div v-if="loadingFiles" class="text-center py-8">Loading files...</div>
             <ResultList v-else :files="jobFiles" @preview="openPreview" />
          </div>
       </div>
    </div>
    
    <!-- PDF Preview Overlay -->
    <PdfPreview 
       :isOpen="!!previewFile" 
       :file="previewFile" 
       @close="previewFile = null" 
    />

  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ArrowLeft, X } from 'lucide-vue-next';
import QueuePanel from '../components/QueuePanel.vue';
import HistoryList from '../components/HistoryList.vue';
import ResultList from '../components/ResultList.vue';
import PdfPreview from '../components/PdfPreview.vue';
import { fetchJobFiles } from '../api';
import type { JobFile } from '../types';

// const historyRef = ref<any>(null);
const selectedJobId = ref('');
const loadingFiles = ref(false);
const jobFiles = ref<JobFile[]>([]);
const previewFile = ref<JobFile | null>(null);

const refreshHistory = () => {
   // Assuming HistoryList exposes a load method via expose or we just remount
   // But standard setup script doesn't expose by default unless defined
   // A simpler way is using a key-changer or just relying on auto-mounted hook
   // Let's rely on standard reload or if HistoryList has a timer.
   // Or better: Let's create a trigger.
   // For now, reload window is brute force. Let's try to call method if ref available?
   // Actually, standard <script setup> components are closed by default.
   // Let's modify HistoryList to expose load method? Or just use key hack.
   // We will implement `defineExpose` in HistoryList in next step if strictly needed,
   // BUT standard page reload is acceptable for "Refresh" button for MVP or we just re-mount using key.
   location.reload(); 
};

const viewDetails = async (id: string) => {
   selectedJobId.value = id;
   loadingFiles.value = true;
   try {
     const res = await fetchJobFiles(id);
     jobFiles.value = res.data;
   } catch (e) {
     alert('Failed to load files');
   } finally {
     loadingFiles.value = false;
   }
};

const openPreview = (file: JobFile) => {
  previewFile.value = file;
};
</script>
