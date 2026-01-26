<template>
  <div class="space-y-4">
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
      <p class="text-gray-500">Loading history...</p>
    </div>

    <div v-else-if="jobs.length === 0" class="text-center py-12 bg-gray-50 rounded-lg">
      <p class="text-gray-500">No translation history found.</p>
    </div>

    <div v-else class="space-y-3">
       <div 
         v-for="job in jobs" 
         :key="job.job_id"
         class="bg-white border rounded-lg p-4 hover:shadow-sm transition-shadow"
       >
         <div class="flex items-start justify-between">
           <div class="flex-1">
              <div class="flex items-center space-x-2">
                <span class="font-medium text-lg text-gray-800">{{ job.folder_name || 'Untitled' }}</span>
                <span 
                  class="px-2 py-0.5 rounded text-xs font-medium capitalize"
                  :class="{
                    'bg-yellow-100 text-yellow-700': job.status === 'queued',
                    'bg-blue-100 text-blue-700': job.status === 'running',
                    'bg-green-100 text-green-700': job.status === 'finished',
                    'bg-red-100 text-red-700': job.status === 'failed',
                    'bg-gray-100 text-gray-600': job.status === 'canceled'
                  }"
                >
                  {{ job.status }}
                </span>
              </div>
              
              <div class="mt-1 text-sm text-gray-500 flex items-center space-x-4">
                 <span>ID: {{ job.job_id.slice(0, 8) }}...</span>
                 <span>{{ formatTime(job.created_at) }}</span>
                 <span v-if="job.renamed_at" class="text-xs text-gray-400">(Renamed: {{ formatTime(job.renamed_at) }})</span>
              </div>

               <div class="mt-2 text-xs flex items-center space-x-2">
                 <span v-if="job.has_mono" class="px-1.5 py-0.5 bg-purple-50 text-purple-600 border border-purple-100 rounded">Mono</span>
                 <span v-if="job.has_dual" class="px-1.5 py-0.5 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded">Dual</span>
              </div>
           </div>

           <div class="flex flex-col space-y-2">
              <button 
                @click="$emit('select', job.job_id)"
                class="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded border border-transparent hover:border-blue-100 transition-colors"
              >
                View Details
              </button>
              
              <button 
                v-if="['finished', 'failed', 'canceled'].includes(job.status)"
                @click="openRename(job)"
                class="px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded border border-transparent hover:border-gray-200 transition-colors"
              >
                Rename
              </button>
           </div>
         </div>
       </div>
    </div>

    <!-- Rename Modal -->
    <div v-if="renameModal.isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h3 class="text-lg font-medium mb-4">Rename Task</h3>
        
        <div class="space-y-4">
           <div>
             <label class="block text-sm font-medium text-gray-700 mb-1">Folder Name (Display Name)</label>
             <input v-model="renameModal.folderName" type="text" class="w-full border rounded px-3 py-2">
           </div>
           <div>
             <label class="block text-sm font-medium text-gray-700 mb-1">Original Filename (Internal)</label>
             <input v-model="renameModal.fileName" type="text" class="w-full border rounded px-3 py-2">
           </div>
           <p v-if="renameModal.error" class="text-sm text-red-500">{{ renameModal.error }}</p>
           <p v-if="renameModal.confirmMessage" class="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
             {{ renameModal.confirmMessage }}
           </p>
        </div>

        <div class="mt-6 flex justify-end space-x-3">
          <button @click="closeRename" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
          <button 
            @click="submitRename" 
            :disabled="renameModal.submitting"
            class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {{ renameModal.confirming ? 'Confirm Rename' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { fetchJobs, renameJob } from '../api';
import type { Job } from '../types';
import { format } from 'date-fns';

const jobs = ref<Job[]>([]);
const loading = ref(false);
const emit = defineEmits(['select']);

const renameModal = reactive({
  isOpen: false,
  jobId: '',
  folderName: '',
  fileName: '',
  error: '',
  submitting: false,
  confirming: false,
  confirmMessage: ''
});

const formatTime = (ts: string) => {
  try {
    return format(new Date(ts), 'yyyy-MM-dd HH:mm:ss');
  } catch {
    return ts;
  }
};

const loadHistory = async () => {
  loading.value = true;
  try {
    const res = await fetchJobs({ limit: 50 });
    jobs.value = res.data.items;
  } catch (e) {
    console.error('Failed to load history', e);
  } finally {
    loading.value = false;
  }
};

const openRename = (job: Job) => {
  renameModal.jobId = job.job_id;
  renameModal.folderName = job.folder_name || '';
  renameModal.fileName = job.original_filename || '';
  renameModal.error = '';
  renameModal.confirming = false;
  renameModal.confirmMessage = '';
  renameModal.isOpen = true;
};

const closeRename = () => {
  renameModal.isOpen = false;
};

const submitRename = async () => {
  renameModal.submitting = true;
  renameModal.error = '';
  
  try {
    const payload = {
      folder_name: renameModal.folderName,
      original_filename: renameModal.fileName,
      confirm: renameModal.confirming
    };

    await renameJob(renameModal.jobId, payload);
    
    // Success
    closeRename();
    await loadHistory();

  } catch (e: any) {
    if (e.response && e.response.status === 409) {
       // Conflict
       const suggestions = e.response.data;
       renameModal.confirming = true;
       renameModal.folderName = suggestions.suggested_folder_name || renameModal.folderName;
       renameModal.fileName = suggestions.suggested_original_filename || renameModal.fileName;
       renameModal.confirmMessage = 'Name conflict detected. Using suggested names. Click Confirm to proceed.';
    } else {
       renameModal.error = e.response?.data?.message || 'Failed to rename';
    }
  } finally {
    renameModal.submitting = false;
  }
};

onMounted(loadHistory);
</script>
