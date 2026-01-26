<template>
  <div v-if="files.length" class="space-y-3">
    <h3 class="text-sm font-medium text-gray-700">Results</h3>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="file in files" 
        :key="file.file_id"
        class="border rounded-lg p-3 hover:shadow-sm transition-shadow bg-white"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center space-x-2">
            <div class="p-2 bg-red-50 rounded">
              <FileIcon class="w-5 h-5 text-red-500" />
            </div>
            <div>
              <p class="font-medium text-sm truncate max-w-[150px]" :title="file.filename">{{ file.filename }}</p>
              <div class="flex items-center space-x-2 text-xs text-gray-500">
                <span class="capitalize">{{ file.type }}</span>
                <span>•</span>
                <span>{{ formatSize(file.size) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex mt-3 space-x-2">
          <a 
            :href="file.url" 
            :download="file.filename"
            class="flex-1 flex items-center justify-center space-x-1 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded border transition-colors"
          >
           <DownloadCloud class="w-3.5 h-3.5" />
           <span>Download</span>
          </a>
          <button 
            @click="$emit('preview', file)"
            class="flex-1 flex items-center justify-center space-x-1 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded border border-blue-100 transition-colors"
          >
            <Eye class="w-3.5 h-3.5" />
            <span>Preview</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { File as FileIcon, DownloadCloud, Eye } from 'lucide-vue-next';
import type { JobFile } from '../types';

defineProps<{
  files: JobFile[];
}>();

defineEmits<{
  (e: 'preview', file: JobFile): void
}>();

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
</script>
