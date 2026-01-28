<template>
  <div 
    class="fixed right-0 top-1/4 z-50 flex flex-col items-end pointer-events-auto group"
  >
    <!-- Rail/Panel Container -->
    <div 
      class="transition-all duration-300 ease-in-out relative flex flex-col bg-white/30 backdrop-blur-md shadow-lg border-l border-t border-b border-white/20"
      :class="[
        isExpanded ? 'w-80 h-[60vh] rounded-l-xl opacity-100 translate-x-0' :
        hasTasks ? 'w-8 py-3 rounded-l-lg opacity-100 translate-x-0 cursor-pointer' : 
        'w-8 h-10 rounded-l-md cursor-pointer opacity-60 hover:opacity-100 hover:w-8 translate-x-0',
        (!hasTasks && !isHovered && !isExpanded) ? '' : '' 
      ]"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
      @click="handleRailClick"
    >
      
      <!-- EXPANDED VIEW -->
      <div v-if="isExpanded" class="flex flex-col h-full w-full overflow-hidden" @click.stop>
          <!-- Header -->
          <div class="flex items-center justify-between p-3 border-b border-white/20 bg-white/40">
              <h3 class="font-medium text-gray-800 text-sm flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse" v-if="queueData.running.length"></span>
                  Queue ({{ queueData.running.length + queueData.queued.length }})
              </h3>
              <div class="flex items-center gap-1">
                 <button @click.stop="maximizeQueue" class="p-1 hover:bg-black/10 rounded text-gray-600" title="Maximize">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                       <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                 </button>
                 <button @click.stop="toggleExpand" class="p-1 hover:bg-black/10 rounded text-gray-600">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                 </button>
              </div>
          </div>

          <!-- Actions -->
          <div class="p-2 border-b border-white/20 bg-white/20 flex gap-2">
              <button 
                  @click="resumeQueueAction()"
                  :disabled="loadingAction"
                  class="flex-1 py-1.5 text-xs font-medium bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                  Resume All
              </button>
          </div>

          <!-- List -->
          <div class="flex-1 overflow-y-auto p-2 space-y-2">
              <div v-if="queueData.running.length === 0 && queueData.queued.length === 0" class="text-center py-4 text-gray-500 text-sm">
                  Queue is empty
              </div>

              <!-- Running -->
              <div v-for="id in queueData.running" :key="id" class="flex items-center gap-2 p-2 bg-white/40 rounded border border-white/20">
                  <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse flex-shrink-0"></div>
                  <div class="min-w-0 flex-1">
                      <div class="text-xs font-medium text-gray-800 truncate" :title="jobNames[id]">{{ jobNames[id] || 'Loading...' }}</div>
                      <div class="text-[10px] text-green-700">Running</div>
                  </div>
              </div>

              <!-- Queued -->
              <div v-for="id in queueData.queued" :key="id" class="flex items-center gap-2 p-2 bg-white/40 rounded border border-white/20">
                  <div class="w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0"></div>
                  <div class="min-w-0 flex-1">
                      <div class="text-xs font-medium text-gray-800 truncate" :title="jobNames[id]">{{ jobNames[id] || 'Loading...' }}</div>
                      <div class="text-[10px] text-yellow-700">Queued</div>
                  </div>
              </div>
          </div>
      </div>

      <!-- COLLAPSED VIEW (Rail) -->
      <template v-else>
        <!-- Toggle Button (Arrow) -->
        <div 
            v-if="hasTasks"
            class="absolute -left-3 top-1/2 -translate-y-1/2 w-3 h-6 bg-white/50 backdrop-blur rounded-l flex items-center justify-center cursor-pointer hover:bg-white transition-colors opacity-0 group-hover:opacity-100"
            @click.stop="toggleExpand"
        >
             <svg class="w-2 h-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
             </svg>
        </div>

        <!-- Content: Dots -->
        <div 
            v-if="hasTasks"
            class="flex flex-col space-y-2 overflow-y-auto scrollbar-hide px-2 w-full items-center py-2"
            style="max-height: 50vh;"
        >
            <div 
            v-for="id in queueData.running" 
            :key="'run-'+id" 
            class="w-3 h-3 rounded-full bg-green-500 shadow-sm animate-pulse flex-shrink-0 cursor-pointer relative"
            @mouseenter="hoveredJobId = id"
            @mouseleave="hoveredJobId = null"
            ></div>
            <div 
            v-for="id in queueData.queued" 
            :key="'q-'+id" 
            class="w-3 h-3 rounded-full bg-yellow-400 shadow-sm flex-shrink-0 cursor-pointer relative"
            @mouseenter="hoveredJobId = id"
            @mouseleave="hoveredJobId = null"
            ></div>
        </div>

        <!-- Content: Arrow (Empty State) -->
        <div v-else class="flex items-center justify-center w-full h-full text-gray-500" @click="toggleExpand">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
        </div>
      </template>

    </div>

    <!-- Tooltip (Only show when NOT expanded) -->
    <div 
        v-if="!isExpanded && hoveredJobId && jobNames[hoveredJobId]"
        class="absolute right-12 z-50 px-2 py-1 bg-gray-800 text-white text-xs rounded shadow-lg whitespace-nowrap pointer-events-none transition-opacity duration-200"
        :style="{ top: '50%', transform: 'translateY(-50%)' }" 
    >
        {{ jobNames[hoveredJobId] }}
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { fetchQueue, fetchJob, resumeQueue } from '../api';

const router = useRouter();
const queueData = ref({
  max_running: 0,
  running: [] as string[],
  queued: [] as string[]
});
const isHovered = ref(false);
const isExpanded = ref(false);
const hoveredJobId = ref<string | null>(null);
const jobNames = ref<Record<string, string>>({});
const loadingAction = ref(false);

const hasTasks = computed(() => {
  return queueData.value.running.length > 0 || queueData.value.queued.length > 0;
});

let pollInterval: any = null;

const loadQueue = async () => {
  try {
    const res = await fetchQueue();
    // Detect changes to fetch missing names
    const newIds = [...res.data.running, ...res.data.queued];
    
    // Fetch details for any ID we don't have a name for yet
    newIds.forEach(id => {
        if (!jobNames.value[id]) {
            fetchJobName(id);
        }
    });

    queueData.value = res.data;
  } catch (e) {
    // Silent fail for polling
  }
};

const fetchJobName = async (id: string) => {
    try {
        const res = await fetchJob(id);
        if (res.data) {
            const name = res.data.display_name || res.data.original_filename || res.data.folder_name || 'Untitled';
            jobNames.value[id] = name;
        }
    } catch {
        jobNames.value[id] = 'Loading...';
    }
};

const toggleExpand = () => {
    isExpanded.value = !isExpanded.value;
    if (isExpanded.value) {
        hoveredJobId.value = null; // Clear tooltip
    }
};

const handleMouseEnter = () => {
    isHovered.value = true;
};
const handleMouseLeave = () => {
    isHovered.value = false;
};
const handleRailClick = () => {
    if (!hasTasks.value && !isExpanded.value) {
        isExpanded.value = true;
    }
};

const maximizeQueue = () => {
    router.push('/queue');
    isExpanded.value = false; // Collapse rail when navigating
};

const resumeQueueAction = async () => {
    loadingAction.value = true;
    try {
        await resumeQueue({ mode: 'all' });
        await loadQueue();
    } catch (e) {
        alert('Failed to resume');
    } finally {
        loadingAction.value = false;
    }
};

onMounted(() => {
  loadQueue();
  pollInterval = setInterval(loadQueue, 2000);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});
</script>

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
/* Hide scrollbar for IE, Edge and Firefox */
.scrollbar-hide {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
}
</style>
