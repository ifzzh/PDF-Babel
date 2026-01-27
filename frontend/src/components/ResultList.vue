<template>
  <div v-if="files.length" class="space-y-3">
    <!-- Source Files -->
    <div v-if="sourceFiles.length" class="space-y-2">
       <h4 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Original</h4>
       <div class="grid grid-cols-1 gap-4">
         <div 
           v-for="file in sourceFiles" 
           :key="file.file_id"
           class="border rounded-lg p-3 hover:shadow-sm transition-shadow bg-white"
         >
            <div class="flex items-start justify-between">
              <div class="flex items-center space-x-2">
                <div class="p-2 bg-red-50 rounded">
                  <FileIcon class="w-5 h-5 text-red-500" />
                </div>
                <div>
                  <p class="font-medium text-sm truncate max-w-[200px]" :title="file.filename">{{ file.filename }}</p>
                  <div class="flex items-center space-x-2 text-xs text-gray-500">
                    <span class="capitalize">{{ file.type }}</span>
                    <span>•</span>
                    <span>{{ formatSize(file.size) }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex mt-3 space-x-2">
               <!-- Actions reused -->
               <a :href="file.url" :download="file.filename" class="action-btn-download">
                  <DownloadCloud class="w-3.5 h-3.5" /> <span>Download</span>
               </a>
               <button @click="$emit('preview', file)" class="action-btn-preview">
                  <Eye class="w-3.5 h-3.5" /> <span>Preview</span>
               </button>
            </div>
         </div>
       </div>
    </div>

    <!-- Generated Files -->
    <div v-if="resultFiles.length" class="space-y-2">
        <h4 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Results</h4>
        <div class="grid grid-cols-2 gap-4">
          <div 
            v-for="file in resultFiles" 
            :key="file.file_id"
            class="border rounded-lg p-3 hover:shadow-sm transition-shadow bg-white"
          >
             <div class="flex items-start justify-between">
               <div class="flex items-center space-x-2">
                 <div class="p-2 bg-purple-50 rounded">
                   <FileIcon class="w-5 h-5 text-purple-500" />
                 </div>
                 <div class="min-w-0">
                   <p class="font-medium text-sm truncate w-full" :title="file.filename">{{ file.filename }}</p>
                   <div class="flex items-center space-x-2 text-xs text-gray-500">
                     <span class="capitalize">{{ file.type }}</span>
                     <span>•</span>
                     <span>{{ formatSize(file.size) }}</span>
                   </div>
                 </div>
               </div>
             </div>
             
             <div class="flex mt-3 space-x-2">
                <a :href="file.url" :download="file.filename" class="action-btn-download">
                   <DownloadCloud class="w-3.5 h-3.5" /> <span>Download</span>
                </a>
                <button @click="$emit('preview', file)" class="action-btn-preview">
                   <Eye class="w-3.5 h-3.5" /> <span>Preview</span>
                </button>
             </div>
          </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { File as FileIcon, DownloadCloud, Eye } from 'lucide-vue-next';
import type { JobFile } from '../types';

const props = defineProps<{
  files: JobFile[];
}>();

defineEmits<{
  (e: 'preview', file: JobFile): void
}>();

const sourceFiles = computed(() => {
    return props.files.filter(f => f.type === 'source' || f.type === 'original');
});

const resultFiles = computed(() => {
    return props.files.filter(f => ['mono', 'dual', 'result'].includes(f.type) || (f.type !== 'source' && f.type !== 'original'));
});

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
</script>

<style scoped>
.action-btn-download {
 @apply flex-1 flex items-center justify-center space-x-1 px-2 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded border transition-colors;
}
.action-btn-preview {
 @apply flex-1 flex items-center justify-center space-x-1 px-2 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded border border-blue-100 transition-colors;
}
</style>
