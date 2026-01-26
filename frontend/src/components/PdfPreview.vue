<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
    <div class="relative w-full max-w-6xl h-[90vh] bg-gray-100 rounded-lg flex flex-col overflow-hidden">
      <!-- Toolbar -->
      <div class="bg-white px-4 py-2 border-b flex items-center justify-between shadow-sm z-10">
        <h3 class="font-medium text-gray-700 truncate pr-4">{{ file?.filename }}</h3>
        
        <div class="flex items-center space-x-4">
           <div class="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
             <button @click="page > 1 && page--" :disabled="page <= 1" class="p-1 hover:bg-white rounded disabled:opacity-30">
               <ChevronLeft class="w-5 h-5" />
             </button>
             <span class="text-sm font-medium w-16 text-center">{{ page }} / {{ numPages }}</span>
             <button @click="page < numPages && page++" :disabled="page >= numPages" class="p-1 hover:bg-white rounded disabled:opacity-30">
               <ChevronRight class="w-5 h-5" />
             </button>
           </div>
           
           <div class="flex items-center space-x-2 bg-gray-100 rounded-lg p-1 h-9">
              <button @click="scale = Math.max(0.5, scale - 0.2)" class="p-1 hover:bg-white rounded font-bold px-2">-</button>
              <span class="text-xs w-12 text-center">{{ Math.round(scale * 100) }}%</span>
              <button @click="scale = Math.min(3, scale + 0.2)" class="p-1 hover:bg-white rounded font-bold px-2">+</button>
           </div>
        </div>

        <button @click="$emit('close')" class="p-2 hover:bg-red-50 text-gray-500 hover:text-red-500 rounded-full transition-colors">
          <X class="w-6 h-6" />
        </button>
      </div>

      <!-- Canvas Container -->
      <div class="flex-1 overflow-auto flex justify-center p-8 relative bg-gray-500/10">
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
          <div class="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <div class="shadow-lg">
           <canvas :ref="canvasCallback"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { X, ChevronLeft, ChevronRight } from 'lucide-vue-next';
// Import specific build to ensure matching ESM version
import * as pdfjsLib from 'pdfjs-dist';
// Let Vite handle the worker URL to ensure version consistency
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import type { JobFile } from '../types';

// Set worker source to the Vite-resolved URL
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

const props = defineProps<{
  file: JobFile | null;
  isOpen: boolean;
}>();

const emit = defineEmits(['close']);

const pdfDoc = ref<any>(null);
const page = ref(1);
const numPages = ref(0);
const scale = ref(1.2);
const loading = ref(false);
const canvasRef = ref<HTMLCanvasElement | null>(null);

// Handle canvas ref via callback to ensure availability
const canvasCallback = (el: any) => {
  if (el) {
    canvasRef.value = el;
    // only render if we have the doc and haven't rendered this page yet?
    // actually renderPage is cheap if doc exists.
    if (pdfDoc.value) renderPage(page.value);
  }
};

const loadPdf = async () => {
  if (!props.file) return;
  loading.value = true;
  console.log('Loading PDF:', props.file.url);
  
  try {
    // PDF.js supports HTTP Range requests automatically via rangeChunkSize
    // default is generally 64k. 
    // We just pass the URL, pdf.js handles the rest if server supports Range (backend contract says yes).
    // CRITICAL: specific cMapUrl is required for correct rendering of CJK characters in many PDFs
    // We serve these locally from /public/cmaps and /public/standard_fonts to ensure version match
    const loadingTask = pdfjsLib.getDocument({
      url: props.file.url,
      cMapUrl: '/cmaps/',
      cMapPacked: true,
      standardFontDataUrl: '/standard_fonts/',
    });
    pdfDoc.value = await loadingTask.promise;
    console.log('PDF Loaded, pages:', pdfDoc.value.numPages);
    numPages.value = pdfDoc.value.numPages;
    page.value = 1;
    renderPage(1);
  } catch (err) {
    console.error('Error loading PDF:', err);
    alert('Failed to load PDF preview: ' + err);
  } finally {
    loading.value = false;
  }
};

const renderPage = async (num: number) => {
  if (!pdfDoc.value) {
      console.warn('renderPage called but pdfDoc is null');
      return;
  }
  if (!canvasRef.value) {
      console.warn('renderPage called but canvasRef is null');
      return;
  }
  
  loading.value = true;
  try {
    console.log('Rendering page', num);
    const pageData = await pdfDoc.value.getPage(num);
    const viewport = pageData.getViewport({ scale: scale.value });
    const canvas = canvasRef.value;
    const ctx = canvas.getContext('2d');

    if (!ctx) {
        console.error('Canvas context is null');
        return;
    }

    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
      canvasContext: ctx,
      viewport: viewport
    };

    await pageData.render(renderContext).promise;
    console.log('Page rendered successfully');
  } catch(e) {
    console.error('Render error:', e);
    alert('Render error: ' + e);
  } finally {
    loading.value = false;
  }
};

watch(() => props.isOpen, (newVal) => {
  if (newVal && props.file) {
    loadPdf();
  } else {
    pdfDoc.value = null;
    numPages.value = 0;
  }
});

watch([page, scale], () => {
    // Debounce slightly or just render
    renderPage(page.value);
});

// Close on Escape
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) emit('close');
};

onMounted(() => window.addEventListener('keydown', handleKeydown));
onUnmounted(() => window.removeEventListener('keydown', handleKeydown));
</script>
