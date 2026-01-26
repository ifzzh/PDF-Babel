<template>
  <div 
    class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer"
    :class="[
      isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400',
      error ? 'border-red-500 bg-red-50' : ''
    ]"
    @dragenter.prevent="isDragging = true"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
    @click="triggerFileInput"
  >
    <input 
      type="file" 
      ref="fileInput" 
      class="hidden" 
      accept=".pdf" 
      @change="handleFileSelect"
    >
    
    <div v-if="selectedFile" class="flex items-center justify-center space-x-2 w-full px-4">
      <FileText class="w-8 h-8 text-blue-600 flex-shrink-0" />
      <span class="font-medium text-gray-700 truncate max-w-[150px] md:max-w-xs" :title="selectedFile.name">{{ selectedFile.name }}</span>
      <span class="text-sm text-gray-500 flex-shrink-0">({{ formatSize(selectedFile.size) }})</span>
      <button @click.stop="clearFile" class="p-1 hover:bg-gray-200 rounded-full flex-shrink-0">
        <X class="w-4 h-4 text-gray-500" />
      </button>
    </div>
    
    <div v-else>
      <UploadCloud class="w-12 h-12 text-gray-400 mx-auto mb-3" />
      <p class="text-gray-600 font-medium">Click or drag PDF file here to upload</p>
      <p class="text-sm text-gray-400 mt-1">Only .pdf files are supported</p>
    </div>

    <p v-if="error" class="text-red-500 text-sm mt-2">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { UploadCloud, FileText, X } from 'lucide-vue-next';

const emit = defineEmits(['select']);
const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);
const selectedFile = ref<File | null>(null);
const error = ref('');

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const validateFile = (file: File) => {
  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    error.value = 'Invalid file type. Please upload a PDF.';
    return false;
  }
  error.value = '';
  return true;
};

const handleFile = (file: File) => {
  if (validateFile(file)) {
    selectedFile.value = file;
    emit('select', file);
  }
};

const handleDrop = (e: DragEvent) => {
  isDragging.value = false;
  if (e.dataTransfer?.files.length) {
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }
};

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement;
  if (input.files?.length) {
    const file = input.files[0];
    if (file) handleFile(file);
  }
};

const triggerFileInput = () => fileInput.value?.click();

const clearFile = () => {
  selectedFile.value = null;
  if (fileInput.value) fileInput.value.value = '';
  emit('select', null);
};
</script>
