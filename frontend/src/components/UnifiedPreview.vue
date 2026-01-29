<template>
  <div class="flex flex-col h-full w-full bg-gray-100 overflow-hidden relative">
      <!-- Scrollable Container -->
      <div 
         ref="containerRef"
         class="flex-1 overflow-auto bg-gray-200/50 relative"
         @wheel.ctrl.prevent="handleWheel"
      >

          <!-- Content: PDF (canvas render via PDF.js) -->
          <div v-if="isPdf && url" class="flex flex-col items-center gap-4">
              <div v-if="loadingPdf" class="text-gray-500 text-sm">Loading PDF...</div>
              <canvas
                 v-for="page in pageNumbers"
                 :key="page"
                 :ref="setCanvasRef(page)"
                 class="bg-white shadow"
              ></canvas>
          </div>

          <!-- Content: Glossary -->
          <div v-else-if="isGlossary && file" class="w-full h-full">
              <GlossaryTable :file="file" />
          </div>

          <!-- Fallback -->
          <div v-else class="flex flex-col items-center justify-center p-8 bg-white border border-dashed rounded text-gray-400 w-full h-full">
               <p>Preview not available</p>
               <a v-if="url" :href="url" download class="text-blue-600 underline text-sm mt-2">Download</a>
          </div>
      </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick, shallowRef } from 'vue';
import { getDocument, GlobalWorkerOptions, type PDFDocumentProxy } from 'pdfjs-dist/legacy/build/pdf.mjs';
import workerSrc from 'pdfjs-dist/legacy/build/pdf.worker.min.mjs?url';
import GlossaryTable from './GlossaryTable.vue';

GlobalWorkerOptions.workerSrc = workerSrc;


const props = defineProps<{
    file?: any;
    url?: string;
    fileName?: string;
    // Controlled props
    scale?: number;
    fitMode?: 'width' | 'height' | 'manual';
    fitScale?: number;
}>();

const emit = defineEmits<{
    (e: 'update:scale', value: number): void;
    (e: 'update:fitMode', value: 'width' | 'height' | 'manual'): void;
    (e: 'update:fitScale', value: number): void;
}>();

// Utils
const isPdf = computed(() => {
    const name = props.fileName || props.file?.filename || props.file?.name || '';
    return name.toLowerCase().endsWith('.pdf');
});

const isGlossary = computed(() => {
    if (props.file?.type === 'glossary') return true;
    const name = props.fileName || props.file?.filename || props.file?.name || '';
    return name.toLowerCase().endsWith('.csv');
});

// State
const containerRef = ref<HTMLElement | null>(null);
const loadingPdf = ref(false);
const pdfDoc = shallowRef<PDFDocumentProxy | null>(null);
const loadingTask = shallowRef<any | null>(null);
const pageCount = ref(0);
const pageBaseSize = ref<{ width: number; height: number } | null>(null);
const pageNumbers = computed(() =>
    Array.from({ length: pageCount.value }, (_, i) => i + 1)
);
const canvasMap = new Map<number, HTMLCanvasElement>();
const renderTasks = new Map<number, any>();

// Use local state that syncs with props for smooth rendering, but source of truth is prop
const currentScale = computed({
    get: () => props.scale ?? 1.0,
    set: (val) => emit('update:scale', val)
});

const setCanvasRef = (pageNum: number) => (el: HTMLCanvasElement | null) => {
    if (el) {
        canvasMap.set(pageNum, el);
    } else {
        canvasMap.delete(pageNum);
    }
};


// Actions
const setScale = (newScale: number) => {
    const val = Math.min(Math.max(newScale, 0.1), 5.0);
    emit('update:scale', val);
    if (props.fitMode !== 'manual') emit('update:fitMode', 'manual');
};

const handleWheel = (e: WheelEvent) => {
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setScale(currentScale.value + delta);
};

const calcFitScale = (mode: 'width' | 'height') => {
    if (!containerRef.value) return 1.0;
    const base = pageBaseSize.value ?? { width: 800, height: 1132 };
    // Remove padding subtraction to fill the container
    const cw = containerRef.value.clientWidth; 
    const ch = containerRef.value.clientHeight;
    
    // Safety check for zero dimensions
    if (cw <= 0 || ch <= 0) return 1.0;

    let s = 1.0;
    if (mode === 'width') {
        s = cw / base.width;
    } else {
        s = ch / base.height;
        // User request: Cap at 100% for height fit
        s = Math.min(s, 1.0);
    }
    return s;
};

const applyFit = (mode: 'width' | 'height') => {
    const s = calcFitScale(mode);
    emit('update:scale', s);
    emit('update:fitScale', s);
    // Don't emit fitMode update here if we are just reapplying, 
    // but the parent setting fitMode triggers this typically.
};

const cancelRenderTasks = () => {
    for (const task of renderTasks.values()) {
        try {
            task.cancel();
        } catch {
            // ignore
        }
    }
    renderTasks.clear();
};

const cleanupPdf = async () => {
    cancelRenderTasks();
    pageCount.value = 0;
    pageBaseSize.value = null;
    if (loadingTask.value) {
        try {
            await loadingTask.value.destroy();
        } catch {
            // ignore
        }
        loadingTask.value = null;
    }
    if (pdfDoc.value) {
        try {
            await pdfDoc.value.destroy();
        } catch {
            // ignore
        }
        pdfDoc.value = null;
    }
};

const renderPage = async (pageNum: number) => {
    if (!pdfDoc.value) return;
    const canvas = canvasMap.get(pageNum);
    if (!canvas) return;
    const page = await pdfDoc.value.getPage(pageNum);
    const viewport = page.getViewport({ scale: currentScale.value });
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const outputScale = window.devicePixelRatio || 1;
    canvas.width = Math.floor(viewport.width * outputScale);
    canvas.height = Math.floor(viewport.height * outputScale);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    const renderContext: any = {
        canvasContext: ctx,
        viewport,
    };
    if (outputScale !== 1) {
        renderContext.transform = [outputScale, 0, 0, outputScale, 0, 0];
    }

    const task = page.render(renderContext);
    renderTasks.set(pageNum, task);
    try {
        await task.promise;
    } catch {
        // ignore render cancel errors
    }
};

const renderAllPages = async () => {
    if (!pdfDoc.value) return;
    cancelRenderTasks();
    for (const pageNum of pageNumbers.value) {
        // render sequentially to reduce spikes
        await renderPage(pageNum);
    }
};

const loadPdf = async (url: string) => {
    await cleanupPdf();
    loadingPdf.value = true;
    try {
        const task = getDocument(url);
        loadingTask.value = task;
        const doc = await task.promise;
        pdfDoc.value = doc;
        pageCount.value = doc.numPages;

        const firstPage = await doc.getPage(1);
        const viewport = firstPage.getViewport({ scale: 1 });
        pageBaseSize.value = { width: viewport.width, height: viewport.height };

        await nextTick();
        await renderAllPages();
    } finally {
        loadingPdf.value = false;
    }
};

// React to Fit Mode changes from Parent
watch(() => props.fitMode, (newMode) => {
    if (newMode && newMode !== 'manual') {
        nextTick(() => applyFit(newMode));
    }
}, { immediate: true });

// React to URL changes (reset to fit height usually?)
watch(() => props.url, async (newUrl) => {
    if (isPdf.value && newUrl) {
        await loadPdf(newUrl);
        nextTick(() => {
            // Default to Fit Height on new file
            if (props.fitMode && props.fitMode !== 'manual') {
                 applyFit(props.fitMode);
            } else {
                 // Force height fit on load as good default
                 emit('update:fitMode', 'height');
            }
        });
    } else {
        await cleanupPdf();
    }
}, { immediate: true });

// Re-render when scale changes
watch(() => currentScale.value, () => {
    if (pdfDoc.value) {
        renderAllPages();
    }
});

// Resize Observer to keep fit
let observer: ResizeObserver;
onMounted(() => {
    if (containerRef.value) {
        observer = new ResizeObserver(() => {
            if (props.fitMode && props.fitMode !== 'manual') {
                applyFit(props.fitMode);
            }
        });
        observer.observe(containerRef.value);
    }
});

onUnmounted(() => {
    if (observer && containerRef.value) {
        observer.disconnect();
    }
    cleanupPdf();
});
</script>
