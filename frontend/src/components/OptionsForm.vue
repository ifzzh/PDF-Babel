<template>
  <div class="space-y-6">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Source Language</label>
        <input v-model="form.lang_in" type="text" class="w-full border rounded-md px-3 py-2 bg-gray-50 text-gray-500" readonly />
        <p class="text-xs text-gray-400 mt-1">Auto-detected (or locked to 'en' for MVP)</p>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Target Language</label>
        <select v-model="form.lang_out" class="w-full border rounded-md px-3 py-2">
          <option value="zh">Chinese (zh)</option>
          <option value="en">English (en)</option>
          <option value="ja">Japanese (ja)</option>
        </select>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Pages (Optional)</label>
      <input 
        v-model="form.pages" 
        type="text" 
        placeholder="e.g. 1-5, 8, 11-13" 
        class="w-full border rounded-md px-3 py-2"
      >
    </div>

    <div>
      <h3 class="text-sm font-medium text-gray-700 mb-2">Advanced Options</h3>
      <div class="space-y-2 border rounded-md p-4 bg-gray-50">
        <div class="flex items-center justify-between">
            <span class="text-sm">Skip Clean</span>
            <input type="checkbox" v-model="form.skip_clean">
        </div>
        <div class="flex items-center justify-between">
            <span class="text-sm">Enhance Compatibility</span>
            <input type="checkbox" v-model="form.enhance_compatibility">
        </div>
        <div class="flex items-center justify-between">
            <span class="text-sm">Split Short Lines</span>
            <input type="checkbox" v-model="form.split_short_lines">
        </div>
        <div class="flex items-center justify-between">
            <span class="text-sm">Short Line Split Factor</span>
             <input type="number" step="0.1" v-model.number="form.short_line_split_factor" class="w-20 border rounded px-1 text-right">
        </div>
        <div class="flex items-center justify-between">
            <span class="text-sm">Skip Scanned Detection</span>
            <input type="checkbox" v-model="form.skip_scanned_detection">
        </div>
         <div class="flex items-center justify-between">
            <span class="text-sm">OCR Workaround</span>
            <input type="checkbox" v-model="form.ocr_workaround">
        </div>
         <div class="flex items-center justify-between">
            <span class="text-sm">Auto Enable OCR Workaround</span>
            <input type="checkbox" v-model="form.auto_enable_ocr_workaround">
        </div>
         <div class="flex items-center justify-between">
            <span class="text-sm">Auto Extract Glossary</span>
            <input type="checkbox" v-model="form.auto_extract_glossary">
        </div>
        
        <div class="pt-2 border-t">
           <label class="block text-xs font-medium text-gray-600 mb-1">Custom System Prompt</label>
           <textarea v-model="form.custom_system_prompt" class="w-full text-xs border rounded p-2" rows="2"></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue';

const emit = defineEmits(['update:options']);

const form = reactive({
  lang_in: 'en',
  lang_out: 'zh',
  pages: '',
  // Advanced defaults
  skip_clean: false,
  enhance_compatibility: false,
  split_short_lines: false,
  short_line_split_factor: 0.8,
  skip_scanned_detection: false,
  ocr_workaround: false,
  auto_enable_ocr_workaround: false,
  auto_extract_glossary: true,
  custom_system_prompt: '',
  pool_max_workers: 8,
  term_pool_max_workers: 4
});

watch(form, (newVal) => {
  emit('update:options', { ...newVal });
}, { deep: true, immediate: true });
</script>
