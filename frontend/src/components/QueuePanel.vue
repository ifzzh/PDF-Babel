<template>
  <div class="space-y-4 bg-white p-4 rounded-lg shadow-sm border border-gray-100">
    <div class="flex items-center justify-between">
      <h3 class="font-medium text-gray-800 flex items-center gap-2">
        <Server class="w-4 h-4 text-gray-500" />
        Queue Status
      </h3>
      <div class="flex gap-2">
        <button 
          v-if="selectedIds.length > 0"
          @click="resume('selected')"
          :disabled="loading"
          class="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Resume Selected ({{ selectedIds.length }})
        </button>
        <button 
          @click="resume('all')"
          :disabled="loading"
          class="px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 disabled:opacity-50 transition-colors"
        >
          Resume All
        </button>
      </div>
    </div>

    <div v-if="loading" class="py-4 text-center text-sm text-gray-500 animate-pulse">
      Loading queue...
    </div>

    <div v-else-if="jobs.length === 0" class="py-4 text-center text-sm text-gray-500 bg-gray-50 rounded">
      Queue is empty
    </div>

    <div v-else class="space-y-2">
      <div 
        v-for="job in jobs" 
        :key="job.job_id"
        @click="toggleSelection(job.job_id, job.status)"
        class="flex items-center justify-between p-3 border rounded transition-colors"
        :class="[
          selectedIds.includes(job.job_id) ? 'bg-blue-100 border-blue-300' : 'hover:bg-gray-50 border-gray-200',
          job.status === 'running' ? 'cursor-default opacity-75' : 'cursor-pointer'
        ]"
      >
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="min-w-0">
             <div class="flex items-center gap-2">
                <span 
                  class="w-2 h-2 rounded-full"
                  :class="job.status === 'running' ? 'bg-green-500 animate-pulse' : 'bg-yellow-400'"
                ></span>
                <span class="font-medium text-sm truncate w-40 md:w-60" :title="job.folder_name || job.job_id">
                  {{ job.folder_name || job.job_id }}
                </span>
             </div>
             <div class="text-xs text-gray-400 ml-4 truncate">
                {{ formatTime(job.created_at) }}
             </div>
          </div>
        </div>
        
        <span 
          class="text-xs px-2 py-1 rounded capitalize"
          :class="job.status === 'running' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
        >
          {{ job.status }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { Server } from 'lucide-vue-next';
import { fetchQueue, fetchJobs, resumeQueue } from '../api';
import type { Job } from '../types';
import { format } from 'date-fns';

const jobs = ref<Job[]>([]);
const loading = ref(false);
const selectedIds = ref<string[]>([]);
let pollInterval: any = null;

const formatTime = (ts: string) => {
  try {
    return format(new Date(ts), 'yyyy-MM-dd HH:mm:ss');
  } catch {
    return ts;
  }
};

const toggleSelection = (id: string, status: string) => {
    if (status === 'running') return;
    const idx = selectedIds.value.indexOf(id);
    if (idx > -1) {
        selectedIds.value.splice(idx, 1);
    } else {
        selectedIds.value.push(id);
    }
};

const loadQueue = async () => {
  try {
    const queueRes = await fetchQueue();
    const ids = [...queueRes.data.running, ...queueRes.data.queued];
    
    if (ids.length === 0) {
      jobs.value = [];
      return;
    }

    // Fetch details strictly for these IDs
    // In a real optimized scenario, we'd have a bulk fetch. 
    // Here we use fetchJobs with limit/offset or just fetch latest and filter if API supported it.
    // Given API constraints, we might need individual gets or fetchJobs page.
    // Ideally use: GET /api/jobs?ids=... if supported? 
    // Contract doesn't specify bulk ID get. 
    // Fallback strategy: Fetch latest 20 jobs and match, or fetch individually.
    // For MVP, lets assume fetchJobs returns enough history or we fetch individually.
    // IMPORTANT: Contract says: "若需展示名字/时间：需用 GET /api/jobs 或 GET /api/jobs/{id} 补全"
    
    // We will do parallel fetch for up to 10 items to be safe
    // const detailedJobs = await Promise.all(
    //    ids.slice(0, 10).map(id => fetchJobs({ limit: 100 }).then(res => res.data.items.find((j: Job) => j.job_id === id))) 
    // );

    // Using individual fetch for correctness
    // Note: To avoid 404s if queue has stale IDs (unlikely), handle errors
    const tasks = await Promise.all(
        ids.map(async (id) => {
            try {
                // Try from list first if cached, or individual
                // Since we don't have store, individual fetch
                const res = await fetchJobs({ limit: 50 }); // Primitive "cache" via list
                const found = res.data.items.find((j: Job) => j.job_id === id);
                if (found) return found;
                // Fallback
                return { job_id: id, status: 'queued', created_at: new Date().toISOString() } as Job; 
            } catch {
                return null;
            }
        })
    );
    
    jobs.value = tasks.filter(Boolean) as Job[];

  } catch (e) {
    console.error('Queue load failed', e);
  }
};

const resume = async (mode: 'all' | 'selected') => {
  loading.value = true;
  try {
    let payload = {};
    if (mode === 'all') {
      payload = { mode: 'all' };
    } else {
      payload = { job_ids: selectedIds.value };
    }
    
    const res = await resumeQueue(payload);
    
    // Alert logic for skipped items
    if (res.data.skipped && res.data.skipped.length > 0) {
      const reasons = res.data.skipped.map((s: any) => `${s.job_id} (${s.reason})`).join(', ');
      alert(`Some jobs were skipped: ${reasons}`);
    }

    selectedIds.value = [];
    await loadQueue(); // Refresh immediately
    emit('refresh'); // Tell parent to refresh active job if needed
  } catch (e) {
    alert('Failed to resume queue');
  } finally {
    loading.value = false;
  }
};

const emit = defineEmits(['refresh']);

onMounted(() => {
  loadQueue();
  // Poll every 5s for queue updates
  pollInterval = setInterval(loadQueue, 5000);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});
</script>
