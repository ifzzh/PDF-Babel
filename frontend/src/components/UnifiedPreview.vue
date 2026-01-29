<template>
  <div class="flex flex-col h-full w-full bg-gray-100 overflow-hidden relative">
      <!-- Scrollable Container -->
      <div 
         ref="containerRef"
         class="flex-1 overflow-auto bg-gray-200/50 p-4 flex items-center justify-center relative"
         @wheel.ctrl.prevent="handleWheel"
      >
          <!-- Content Wrapper (No Transform) -->
          <div 
             class="bg-white shadow-lg block mx-auto transition-[width,height] duration-150 ease-out"
             :style="{ 
                 width: (baseSize.width * currentScale) + 'px',
                 height: (baseSize.height * currentScale) + 'px'
             }"
          >
               <!-- Content: PDF Iframe -->
               <iframe 
                   v-if="isPdf && url"
                   :src="url + '#toolbar=0'"
                   class="border-none block w-full h-full"
               ></iframe>

               <!-- Content: Glossary -->
               <div v-else-if="isGlossary && file" class="w-full h-full overflow-hidden block">
                   <GlossaryTable :file="file" />
               </div>

               <!-- Fallback -->
               <div v-else class="flex flex-col items-center justify-center p-8 bg-white border border-dashed rounded text-gray-400 w-full h-full">
                    <p>Preview not available</p>
                    <a v-if="url" :href="url" download class="text-blue-600 underline text-sm mt-2">Download</a>
               </div>
          </div>
      </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import GlossaryTable from './GlossaryTable.vue';


const props = defineProps<{
    file?: any;
    url?: string;
    fileName?: string;
    // Controlled props
    scale?: number;
    fitMode?: 'width' | 'height' | 'manual';
}>();

const emit = defineEmits<{
    (e: 'update:scale', value: number): void;
    (e: 'update:fitMode', value: 'width' | 'height' | 'manual'): void;
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

// Use local state that syncs with props for smooth rendering, but source of truth is prop
const currentScale = computed({
    get: () => props.scale ?? 1.0,
    set: (val) => emit('update:scale', val)
});

// Base content dimensions
const baseSize = { width: 800, height: 1132 }; // Approx A4 Ratio 1:1.414


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
    const padding = 40;
    const cw = containerRef.value.clientWidth - padding; 
    const ch = containerRef.value.clientHeight - padding;
    
    // Safety check for zero dimensions
    if (cw <= 0 || ch <= 0) return 1.0;

    let s = 1.0;
    if (mode === 'width') {
        s = cw / baseSize.width;
    } else {
        s = ch / baseSize.height;
    }
    return s;
};

const applyFit = (mode: 'width' | 'height') => {
    const s = calcFitScale(mode);
    emit('update:scale', s);
    // Don't emit fitMode update here if we are just reapplying, 
    // but the parent setting fitMode triggers this typically.
};

// React to Fit Mode changes from Parent
watch(() => props.fitMode, (newMode) => {
    if (newMode && newMode !== 'manual') {
        nextTick(() => applyFit(newMode));
    }
}, { immediate: true });

// React to URL changes (reset to fit height usually?)
watch(() => props.url, () => {
    nextTick(() => {
        // Default to Fit Height on new file
        if (props.fitMode && props.fitMode !== 'manual') {
             applyFit(props.fitMode);
        } else {
             // Force height fit on load as good default
             emit('update:fitMode', 'height');
        }
    });
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
</script>
