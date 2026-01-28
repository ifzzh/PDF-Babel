<template>
  <div class="h-[calc(100vh-64px)] flex overflow-hidden bg-gray-50" @mousemove="handleResize" @mouseup="stopResize" @mouseleave="stopResize">
    <!-- Left Column: Inputs (Resizable Sidebar) -->
    <div 
        class="h-full flex flex-col border-r bg-white shadow-sm z-10 shrink-0 relative group/sidebar"
        :style="{ width: sidebarWidth + 'px' }"
    >
        <!-- Resizer Handle -->
        <div 
            class="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-400 active:bg-blue-600 transition-colors z-50 flex items-center justify-center opacity-0 group-hover/sidebar:opacity-100 active:opacity-100"
            @mousedown.prevent="startResize"
        >
            <!-- visual indicator optional -->
            <div class="h-8 w-0.5 bg-white/50 rounded-full"></div>
        </div>

         <!-- Scrollable Content -->
         <div class="flex-1 overflow-y-auto p-6 space-y-6">
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
         </div>
         
         <!-- Fixed Footer -->
         <div class="p-4 border-t bg-gray-50 flex flex-col gap-3 shrink-0 z-20">
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
              class="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none transition-colors"
            >
              Cancel Task
            </button>
         </div>
    </div>

    <!-- Right Column: Progress & Results -->
    <div class="flex-1 h-full overflow-hidden bg-gray-50 flex flex-col relative">
      
      <!-- Workspace (Review & Results) -->
      <WorkspacePanel 
         v-if="file"
         :source-file="file"
         :result-files="files"
         :job="job"
         class="flex-1"
      />

      <!-- Use placeholder if idle -->
      <div v-else class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg h-full flex-1 flex flex-col items-center justify-center text-gray-400">
         <p class="text-lg font-medium">Ready to translate</p>
         <p class="text-sm">Configure settings on the left and click Start.</p>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import UploadCard from '../components/UploadCard.vue';
import OptionsForm from '../components/OptionsForm.vue';
import SourceSelector from '../components/SourceSelector.vue';
import WorkspacePanel from '../components/WorkspacePanel.vue';
import { useJob } from '../composables/useJob';

const file = ref<File | null>(null);
const options = ref<any>({});
const source = ref<any>(null);

const { job, files, startJob, cancel } = useJob();

// Resizable Sidebar Logic
const sidebarWidth = ref(400); // Default to 400px
const isResizing = ref(false);

const startResize = () => {
  isResizing.value = true;
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';
};

const handleResize = (e: MouseEvent) => {
  if (!isResizing.value) return;
  
  // Constrain width
  const newWidth = e.clientX;
  if (newWidth > 250 && newWidth < 800) {
    sidebarWidth.value = newWidth;
  }
};

const stopResize = () => {
  if (isResizing.value) {
    isResizing.value = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
};

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

</script>
