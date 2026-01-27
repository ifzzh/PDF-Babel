<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    <div class="flex items-center justify-between">
       <h1 class="text-2xl font-bold text-gray-900">PDF Babel Translator</h1>
       <div class="flex items-center space-x-3">
         <router-link to="/history" class="text-sm font-medium text-blue-600 hover:text-blue-500">History & Queue</router-link>
       </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column: Inputs -->
      <div class="lg:col-span-1 space-y-6">
         <!-- Step 1: Upload -->
         <section class="bg-white rounded-lg shadow p-6">
           <h2 class="text-lg font-medium text-gray-900 mb-4">1. Upload PDF</h2>
           <UploadCard @select="handleFileSelect" />
         </section>

         <!-- Step 2: Source -->
         <section class="bg-white rounded-lg shadow p-6 relative">
            <h2 class="text-lg font-medium text-gray-900 mb-4">2. Translation Source</h2>

            <SourceSelector @update:source="handleSourceUpdate" />
         </section>

         <!-- Step 3: Options -->
         <section class="bg-white rounded-lg shadow p-6 relative">
            <h2 class="text-lg font-medium text-gray-900 mb-4">3. Options</h2>

            <OptionsForm @update:options="handleOptionsUpdate" />
         </section>
         
         <div class="pt-4">
            <button 
              @click="submitJob"
              :disabled="!canSubmit || job.status === 'running' || job.status === 'queued'"
              class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span v-if="job.status === 'running'">Translating...</span>
              <span v-else-if="job.status === 'queued'">Queued...</span>
              <span v-else>Start Translation</span>
            </button>
             <button 
              v-if="['running', 'queued'].includes(job.status)"
              @click="cancel"
              class="w-full mt-3 flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none transition-colors"
            >
              Cancel Task
            </button>
         </div>
      </div>

      <!-- Right Column: Progress & Results -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Progress Monitor -->
        <section v-if="job.status !== 'idle'" class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Progress Monitor</h2>
          <ProgressPanel 
             :overall-progress="job.overallProgress"
             :stage-progress="job.stageProgress"
             :stage-name="job.stageName"
             :status="job.status"
             :error="job.error"
             :info="job.info"
          />
        </section>

        <!-- Use placeholder if idle -->
        <div v-else class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg h-96 flex flex-col items-center justify-center text-gray-400">
           <p class="text-lg font-medium">Ready to translate</p>
           <p class="text-sm">Configure settings on the left and click Start.</p>
        </div>

        <!-- Results -->
        <section v-if="files.length > 0" class="bg-white rounded-lg shadow p-6">
           <h2 class="text-lg font-medium text-gray-900 mb-4">Translation Results</h2>
           <ResultList :files="files" @preview="openPreview" />
        </section>
      </div>
    </div>

    <!-- Preview Modal -->
    <PdfPreview 
       :isOpen="!!previewFile" 
       :file="previewFile" 
       @close="previewFile = null" 
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import UploadCard from '../components/UploadCard.vue';
import OptionsForm from '../components/OptionsForm.vue';
import SourceSelector from '../components/SourceSelector.vue';
import ProgressPanel from '../components/ProgressPanel.vue';
import ResultList from '../components/ResultList.vue';
import PdfPreview from '../components/PdfPreview.vue';
import { useJob } from '../composables/useJob';
import type { JobFile } from '../types';

const file = ref<File | null>(null);
const options = ref<any>({});
const source = ref<any>(null);
const previewFile = ref<JobFile | null>(null);

const { job, files, startJob, cancel } = useJob();

const handleFileSelect = (f: File | null) => {
  file.value = f;
};

const handleOptionsUpdate = (opts: any) => {
  options.value = opts;
};

const handleSourceUpdate = (src: any) => {
  source.value = src;
};

const canSubmit = computed(() => {
  return file.value && source.value;
});

const submitJob = () => {
  if (file.value && canSubmit.value) {
    startJob(file.value, options.value, source.value);
  }
};

const openPreview = (f: JobFile) => {
  previewFile.value = f;
};
</script>
