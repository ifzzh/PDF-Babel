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
       <div class="flex items-center space-x-4">
         <!-- Search Bar -->
         <div class="relative flex-1">
           <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
             <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
             </svg>
           </div>
           <input 
             :value="searchQuery"
             @input="handleSearchInput"
             type="text" 
             class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
             placeholder="Search tasks..."
           >
         </div>
         
         <!-- Batch Actions -->
         <div v-if="selectedJobs.size > 0" class="flex items-center space-x-2">
            <span class="text-sm text-gray-500">{{ selectedJobs.size }} selected</span>
            <button 
              @click="confirmDelete()"
              class="px-3 py-2 bg-red-50 text-red-600 rounded hover:bg-red-100 text-sm font-medium transition-colors"
            >
              Delete Selected
            </button>
         </div>
       </div>

       <div v-if="filteredJobs.length === 0" class="text-center py-8 text-gray-500">
         No tasks match your search.
       </div>
       
       <!-- Select All Header (Optional but good for UX) -->
       <div v-if="filteredJobs.length > 0" class="flex items-center px-4 py-2 bg-gray-50 rounded border text-sm text-gray-600">
          <input 
            type="checkbox" 
            :checked="allSelected"
            @change="toggleAll"
            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3 h-4 w-4"
          >
          <span>Select All</span>
       </div>

       <div 
         v-for="job in filteredJobs" 
         :key="job.job_id"
         class="bg-white border rounded-lg p-4 hover:shadow-sm transition-shadow"
         :class="{'ring-2 ring-blue-500 border-transparent': selectedJobs.has(job.job_id)}"
       >
         <div class="flex items-start justify-between">
           <div class="flex items-center mr-4 pt-1">
             <input 
               type="checkbox" 
               :checked="selectedJobs.has(job.job_id)"
               @change="toggleSelection(job.job_id)"
               class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
             >
           </div>
           
           <div class="flex-1">
              <div class="flex items-center space-x-2">
                <span class="font-medium text-lg text-gray-800">{{ stripExtension(job.display_name || job.original_filename || job.folder_name || 'Untitled') }}</span>
                <span v-if="job.original_filename && job.folder_name !== job.original_filename" class="text-xs text-gray-400">({{ job.folder_name }})</span>
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
                style="min-width: 80px"
              >
                Details
              </button>
              
              <button 
                v-if="['finished', 'failed', 'canceled'].includes(job.status)"
                @click="openRename(job)"
                class="px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded border border-transparent hover:border-gray-200 transition-colors"
              >
                Rename
              </button>

              <button 
                @click="confirmDelete(job.job_id)"
                class="px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded border border-transparent hover:border-red-100 transition-colors"
              >
                Delete
              </button>
           </div>
         </div>
       </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="isDeleteModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div class="bg-white rounded-lg p-6 w-full max-w-sm shadow-lg">
            <h3 class="text-lg font-medium text-red-600 mb-2">Confirm Delete</h3>
            <p class="text-gray-600 mb-4">
                {{ deleteTarget ? 'Are you sure you want to delete this task?' : `Are you sure you want to delete ${selectedJobs.size} selected tasks?` }}
                This action cannot be undone.
            </p>
            
            <p v-if="deleteError" class="text-sm text-red-500 mb-4 bg-red-50 p-2 rounded">{{ deleteError }}</p>

            <div class="flex justify-end space-x-3">
                <button @click="isDeleteModalOpen = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                <button @click="processedDelete" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
            </div>
        </div>
    </div>

    <!-- Rename Modal -->
    <div v-if="renameModal.isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h3 class="text-lg font-medium mb-4">Rename Task</h3>
        
        <div class="space-y-4">
           <div>
             <label class="block text-sm font-medium text-gray-700 mb-1">Display Name (Title)</label>
             <div class="flex space-x-2">
                 <input v-model="renameModal.displayName" type="text" class="flex-1 border rounded px-3 py-2">
                 <button @click="syncToFilename" class="px-2 py-1 bg-gray-100 text-xs border rounded hover:bg-gray-200" title="Sync to Filename">
                    Current → Filename
                 </button>
             </div>
           </div>

           <div>
             <label class="block text-sm font-medium text-gray-700 mb-1">Folder Name (Directory)</label>
             <input v-model="renameModal.folderName" type="text" class="w-full border rounded px-3 py-2">
           </div>
           
           <div>
             <label class="block text-sm font-medium text-gray-700 mb-1">Original Filename (Internal)</label>
             <div class="flex space-x-2">
                <input v-model="renameModal.fileName" type="text" class="flex-1 border rounded px-3 py-2">
                <button @click="syncToDisplay" class="px-2 py-1 bg-gray-100 text-xs border rounded hover:bg-gray-200" title="Sync to Display Name">
                    Current → Display
                 </button>
             </div>
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
import { ref, onMounted, reactive, computed } from 'vue';
import { fetchJobs, renameJob, fetchJob, deleteJob, deleteJobs } from '../api';
import type { Job } from '../types';
import { format } from 'date-fns';

const jobs = ref<Job[]>([]);
const loading = ref(false);
const emit = defineEmits(['select']);

// Search State
const searchQuery = ref('');
const debouncedQuery = ref('');
let searchTimeout: any = null;

const handleSearchInput = (e: Event) => {
  const val = (e.target as HTMLInputElement).value;
  searchQuery.value = val;
  
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    debouncedQuery.value = val;
  }, 300);
};

const filteredJobs = computed(() => {
  // ... (previous filter logic remains same, just ensuring context)
  const rawQuery = debouncedQuery.value.trim();
  // ... (omitted filter logic implementation details to keep diff small, assuming context match)
  // Re-implementing filter logic briefly to ensure context is correct or just assume wrap?
  // Actually, I should just supply the new logic additions and let replace match the surrounding.
  // Wait, replace_file_content needs exact match. I'll read file first to be safe or use what I have.
  // I have the content from previous turn.

  if (!rawQuery) return jobs.value;
  
  const keywords = rawQuery.toLowerCase().split(/\s+/).filter(k => k.length > 0);
  if (keywords.length === 0) return jobs.value;

  const scored = jobs.value.map(job => {
    let score = 0;
    const display = (job.display_name || '').toLowerCase();
    const filename = (job.original_filename || '').toLowerCase();
    const folder = (job.folder_name || '').toLowerCase();

    const allMatch = keywords.every(k => {
      const inDisplay = display.includes(k);
      const inFilename = filename.includes(k);
      const inFolder = folder.includes(k);
      if (!inDisplay && !inFilename && !inFolder) return false;
      if (inDisplay) score += 3;
      if (inFilename) score += 2;
      if (inFolder) score += 1;
      return true;
    });
    return { job, score, match: allMatch };
  });

  const matches = scored.filter(item => item.match);
  matches.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return new Date(b.job.created_at).getTime() - new Date(a.job.created_at).getTime();
  });
  return matches.map(item => item.job);
});

// Selection Logic
const selectedJobs = ref<Set<string>>(new Set());
const allSelected = computed(() => {
    return filteredJobs.value.length > 0 && selectedJobs.value.size === filteredJobs.value.length;
});
const toggleSelection = (id: string) => {
    if (selectedJobs.value.has(id)) selectedJobs.value.delete(id);
    else selectedJobs.value.add(id);
};
const toggleAll = () => {
    if (allSelected.value) {
        selectedJobs.value.clear();
    } else {
        filteredJobs.value.forEach(job => selectedJobs.value.add(job.job_id));
    }
};

// Delete Logic
const isDeleteModalOpen = ref(false);
const deleteTarget = ref<string | null>(null); // null means batch delete
const deleteError = ref('');

const confirmDelete = (id?: string) => {
    deleteTarget.value = id || null;
    deleteError.value = '';
    isDeleteModalOpen.value = true;
};

const processedDelete = async () => {
    try {
        if (deleteTarget.value) {
            // Single
            const res = await deleteJob(deleteTarget.value, true);
            if (res.data.status === 'canceling') {
               alert('Job is currently canceling. Please try deleting again later.');
            }
        } else {
            // Batch
            const ids = Array.from(selectedJobs.value);
            const res = await deleteJobs({ job_ids: ids, confirm: true });
            
            const skipped = res.data.skipped || [];
            if (skipped.length > 0) {
                const reasons = skipped.map((s: any) => `${s.job_id}: ${s.reason}`).join('\n');
                alert(`Some jobs could not be deleted:\n${reasons}`);
            }
            selectedJobs.value.clear();
        }
        isDeleteModalOpen.value = false;
        loadHistory();
    } catch (e: any) {
        deleteError.value = e.response?.data?.detail || 'Delete failed';
    }
};

const renameModal = reactive({
  isOpen: false,
// ... (rest of rename modal logic)
  jobId: '',
  folderName: '',
  fileName: '',
  displayName: '',
  error: '',
  submitting: false,
  confirming: false,
  confirmMessage: ''
});
// ...
const formatTime = (ts: string) => {
  try {
    return format(new Date(ts), 'yyyy-MM-dd HH:mm:ss');
  } catch {
    return ts;
  }
};
// ... (stripExtension logic)
const stripExtension = (name: string) => {
  if (!name) return '';
  const lastDot = name.lastIndexOf('.');
  if (lastDot > 0) return name.substring(0, lastDot);
  return name;
};
// ... (loadHistory logic)
const loadHistory = async () => {
  loading.value = true;
  try {
    const res = await fetchJobs({ limit: 50 });
    jobs.value = res.data.items;
    selectedJobs.value.clear(); // clear selection on reload
    
    jobs.value.forEach(async (job) => {
        if (!job.original_filename || job.display_name === undefined) {
            try {
                const detail = await fetchJob(job.job_id);
                if (detail.data) {
                    if (detail.data.original_filename) job.original_filename = detail.data.original_filename;
                    if (detail.data.display_name !== undefined) job.display_name = detail.data.display_name;
                }
            } catch (e) {
                console.warn(`Failed to fetch details for ${job.job_id}`);
            }
        }
    });

  } catch (e) {
    console.error('Failed to load history', e);
  } finally {
    loading.value = false;
  }
};
// ... (rest of rename functions)


const openRename = async (job: Job) => {
  // Use local copy first
  renameModal.jobId = job.job_id;
  renameModal.folderName = job.folder_name || '';
  renameModal.fileName = job.original_filename || '';
  renameModal.displayName = job.display_name || '';
  
  // Reset state
  renameModal.error = '';
  renameModal.confirming = false;
  renameModal.confirmMessage = '';
  renameModal.isOpen = true;

  // Fetch full details to ensure we have latest display_name/filename
  try {
      const res = await fetchJob(job.job_id);
      if (res.data) {
          renameModal.fileName = res.data.original_filename || renameModal.fileName;
          renameModal.folderName = res.data.folder_name || renameModal.folderName;
          renameModal.displayName = res.data.display_name || renameModal.displayName;
      }
  } catch (e) {
      renameModal.error = 'Failed to fetch latest job details';
  }
};

const closeRename = () => {
  renameModal.isOpen = false;
};

// Sync Logic
const syncToFilename = () => {
    if (!renameModal.displayName) return;
    let name = renameModal.displayName.trim();
    if (!name.toLowerCase().endsWith('.pdf')) {
        name += '.pdf';
    }
    renameModal.fileName = name;
};

const syncToDisplay = () => {
    if (!renameModal.fileName) return;
    let name = renameModal.fileName.trim();
    if (name.toLowerCase().endsWith('.pdf')) {
        name = name.slice(0, -4);
    }
    renameModal.displayName = name;
};

const submitRename = async () => {
  renameModal.submitting = true;
  renameModal.error = '';
  
  try {
    const payload = {
      folder_name: renameModal.folderName,
      original_filename: renameModal.fileName,
      display_name: renameModal.displayName,
      confirm: renameModal.confirming
    };

    await renameJob(renameModal.jobId, payload);
    
    // Success
    closeRename();
    await loadHistory();

  } catch (e: any) {
    if (e.response && e.response.status === 409) {
       // Conflict
       const detail = e.response.data.detail || {};
       renameModal.confirming = true;
       if (detail.suggested_folder_name) {
           renameModal.folderName = detail.suggested_folder_name;
       }
       if (detail.suggested_original_filename) {
           renameModal.fileName = detail.suggested_original_filename;
       }
       // Note: display_name likely doesn't conflict, logic depends on backend, but usually it's metadata
       
       renameModal.confirmMessage = 'Name conflict detected. Using suggested names. Click Confirm to proceed.';
    } else {
       const msg = typeof e.response?.data?.detail === 'string' 
            ? e.response.data.detail 
            : (e.response?.data?.message || 'Failed to rename');
       renameModal.error = msg;
    }
  } finally {
    renameModal.submitting = false;
  }
};

onMounted(loadHistory);
</script>
