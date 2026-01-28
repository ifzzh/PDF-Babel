<template>
  <div class="space-y-6">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
          Source Language
          <InfoTooltip :text="OPTIONS_META.lang_in.desc" />
        </label>
        <input v-model="form.lang_in" type="text" class="w-full border rounded-md px-3 py-2 bg-gray-50 text-gray-500" readonly />
        <p class="text-xs text-gray-400 mt-1">Auto-detected (or locked to 'en' for MVP)</p>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
          Target Language
          <InfoTooltip :text="OPTIONS_META.lang_out.desc" />
        </label>
        <select v-model="form.lang_out" class="w-full border rounded-md px-3 py-2">
          <option value="zh">Chinese (zh)</option>
          <option value="en">English (en)</option>
          <option value="ja">Japanese (ja)</option>
        </select>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
        Pages (Optional)
        <InfoTooltip :text="OPTIONS_META.pages.desc" />
      </label>
      <input 
        v-model="form.pages" 
        type="text" 
        placeholder="e.g. 1-5, 8, 11-13" 
        class="w-full border rounded-md px-3 py-2"
      >
    </div>

    <!-- Output & Watermark -->
    <!-- Output & Watermark -->
    <BaseAccordion title="Output & Watermark" :default-open="true">
      <div class="space-y-4">
          <!-- PDF Types -->
          <div>
              <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">PDF Types</h4>
              <div class="flex flex-wrap gap-3">
                  <BasePillOption 
                      v-model="form.no_dual" 
                      label="No Dual PDF" 
                      :desc="OPTIONS_META.no_dual.desc" 
                  />
                  <BasePillOption 
                      v-model="form.no_mono" 
                      label="No Mono PDF" 
                      :desc="OPTIONS_META.no_mono.desc" 
                  />
                  <BasePillOption 
                      v-model="form.only_include_translated_page" 
                      label="Only Translated Pages" 
                      :desc="OPTIONS_META.only_include_translated_page.desc" 
                  />
              </div>
          </div>

          <!-- Separator -->
          <div class="border-t border-gray-200"></div>

          <!-- Watermark -->
          <div>
              <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                   Watermark
                   <InfoTooltip :text="OPTIONS_META.watermark_output_mode.desc" />
              </h4>
              <div class="flex flex-wrap gap-3">
                  <BasePillRadio 
                      v-model="form.watermark_output_mode" 
                      value="no_watermark" 
                      label="No Watermark" 
                  />
                  <BasePillRadio 
                      v-model="form.watermark_output_mode" 
                      value="watermarked" 
                      label="Watermarked" 
                  />
              </div>
          </div>
      </div>
    </BaseAccordion>

    <!-- Performance & Split -->
    <!-- Performance & Split -->
    <BaseAccordion title="Performance & Split" :default-open="false">
      <div class="space-y-4">
          <!-- QPS & Split -->
          <div class="grid grid-cols-2 gap-4">
              <div>
                  <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                      QPS Limit
                      <InfoTooltip :text="OPTIONS_META.qps.desc" />
                  </label>
                  <input 
                      v-model.number="form.qps" 
                      type="number" 
                      min="1"
                      placeholder="Default: 4"
                      class="w-full border rounded-md px-3 py-2 text-sm"
                  >
              </div>
              <div>
                  <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                      Max Pages / Part
                      <InfoTooltip :text="OPTIONS_META.max_pages_per_part.desc" />
                  </label>
                  <input 
                      v-model.number="form.max_pages_per_part" 
                      type="number" 
                      min="1"
                      placeholder="No Split"
                      class="w-full border rounded-md px-3 py-2 text-sm"
                  >
              </div>
          </div>

          <!-- Separator -->
          <div class="border-t border-gray-200"></div>

          <!-- Thread Pools -->
          <div class="grid grid-cols-2 gap-4">
              <div>
                  <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                      Pool Workers
                      <InfoTooltip :text="OPTIONS_META.pool_max_workers.desc" />
                  </label>
                  <input 
                      v-model.number="form.pool_max_workers" 
                      type="number" 
                      min="1"
                      placeholder="Auto"
                      class="w-full border rounded-md px-3 py-2 text-sm"
                  >
              </div>
              <div>
                  <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                      Term Pool Workers
                      <InfoTooltip :text="OPTIONS_META.term_pool_max_workers.desc" />
                  </label>
                  <input 
                      v-model.number="form.term_pool_max_workers" 
                      type="number" 
                      min="1"
                      placeholder="Auto"
                      class="w-full border rounded-md px-3 py-2 text-sm"
                  >
              </div>
          </div>
      </div>
    </BaseAccordion>

    <!-- Advanced Options -->
    <BaseAccordion title="Advanced Options" :default-open="false">
      <div class="space-y-4">
        
        <!-- Pre-processing -->
        <div>
            <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Pre-processing</h4>
            <div class="flex flex-wrap gap-3">
                <BasePillOption 
                  v-model="form.skip_clean" 
                  label="Skip Clean" 
                  :desc="OPTIONS_META.skip_clean.desc" 
                />
                <BasePillOption 
                  v-model="form.enhance_compatibility" 
                  label="Enhance Compatibility" 
                  :desc="OPTIONS_META.enhance_compatibility.desc" 
                />
                 <BasePillOption 
                  v-model="form.skip_scanned_detection" 
                  label="Skip Scanned Detection" 
                  :desc="OPTIONS_META.skip_scanned_detection.desc" 
                />
            </div>
        </div>

        <!-- Compatibility -->
        <div>
            <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Compatibility</h4>
            <div class="flex flex-wrap gap-3">
                <BasePillOption 
                  v-model="form.disable_rich_text_translate" 
                  label="Disable Rich Text" 
                  :desc="OPTIONS_META.disable_rich_text_translate.desc" 
                />
                <BasePillOption 
                  v-model="form.disable_same_text_fallback" 
                  label="Disable Fallback" 
                  :desc="OPTIONS_META.disable_same_text_fallback.desc" 
                />
            </div>
        </div>

        <!-- Separator -->
        <div class="border-t border-gray-200"></div>

        <!-- Typography & Formula -->
        <div>
            <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Typography & Formula</h4>
            <div class="space-y-3">
                <!-- Primary Font Family -->
                <div>
                   <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                       Primary Font Family
                       <InfoTooltip :text="OPTIONS_META.primary_font_family.desc" />
                   </label>
                   <select v-model="form.primary_font_family" class="w-full border rounded-md px-3 py-2 text-sm bg-white">
                       <option :value="null">Auto (Default)</option>
                       <option value="serif">Serif</option>
                       <option value="sans-serif">Sans-serif</option>
                       <option value="script">Script</option>
                   </select>
                </div>
                
                <!-- Formula Hint -->
                <div class="flex flex-wrap gap-3">
                    <BasePillOption 
                      v-model="form.add_formula_placehold_hint" 
                      label="Add Formula Hint" 
                      :desc="OPTIONS_META.add_formula_placehold_hint.desc" 
                    />
                </div>
            </div>
        </div>

        <!-- Separator -->
        <div class="border-t border-gray-200"></div>

        <!-- Layout & OCR -->
        <div>
            <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Layout & OCR</h4>
            <div class="flex flex-wrap gap-3 items-center">
                 <BasePillOption 
                  v-model="form.split_short_lines" 
                  label="Split Short Lines" 
                  :desc="OPTIONS_META.split_short_lines.desc" 
                />
                 <BasePillOption 
                  v-model="form.ocr_workaround" 
                  label="OCR Workaround" 
                  :desc="OPTIONS_META.ocr_workaround.desc" 
                />
                 <BasePillOption 
                  v-model="form.auto_enable_ocr_workaround" 
                  label="Auto Enable OCR" 
                  :desc="OPTIONS_META.auto_enable_ocr_workaround.desc" 
                />
                
                <!-- Short Line Param integrated here or next line -->
                <div class="flex items-center gap-2 ml-2 pl-2 border-l border-gray-200">
                    <span class="text-xs text-gray-500 font-medium">Split Factor</span>
                    <InfoTooltip :text="OPTIONS_META.short_line_split_factor.desc" />
                    <input type="number" step="0.1" v-model.number="form.short_line_split_factor" class="w-16 border rounded px-1 py-0.5 text-right text-xs">
                </div>
            </div>
        </div>

        <!-- Separator -->
        <div class="border-t border-gray-200"></div>

        <!-- Extraction -->
        <div>
             <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Content</h4>
             <div class="flex flex-wrap gap-3">
                 <BasePillOption 
                  v-model="form.auto_extract_glossary" 
                  label="Auto Extract Glossary" 
                  :desc="OPTIONS_META.auto_extract_glossary.desc" 
                />
                 <BasePillOption 
                  v-model="form.save_auto_extracted_glossary" 
                  label="Save Glossary CSV" 
                  :desc="OPTIONS_META.save_auto_extracted_glossary.desc" 
                />
             </div>
        </div>

        <!-- Prompt -->
        <div class="pt-2 border-t border-gray-200">
           <label class="block text-xs font-medium text-gray-600 mb-1 flex items-center gap-1">
             Custom System Prompt
             <InfoTooltip :text="OPTIONS_META.custom_system_prompt.desc" />
           </label>
           <textarea v-model="form.custom_system_prompt" class="w-full text-xs border rounded p-2" rows="2" placeholder="Start with..."></textarea>
        </div>
      </div>
    </BaseAccordion>

    <!-- Debug & Experimental -->
    <BaseAccordion title="Advanced (Experimental)" :default-open="false">
      <div class="space-y-4">
        <div>
           <h4 class="text-xs font-bold text-red-400 uppercase tracking-wider mb-2">Phase 4 Options</h4>
           <div class="flex flex-wrap gap-3">
               <BasePillOption 
                  v-model="form.skip_translation" 
                  label="Skip Translation" 
                  :desc="OPTIONS_META.skip_translation.desc" 
                />
               <BasePillOption 
                  v-model="form.only_parse_generate_pdf" 
                  label="Only Parse & Generate" 
                  :desc="OPTIONS_META.only_parse_generate_pdf.desc" 
                />
           </div>
           <p class="text-xs text-gray-400 mt-2 italic">
             Note: These options significantly reduce the translation pipeline steps.
           </p>
        </div>
      </div>
    </BaseAccordion>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue';
import InfoTooltip from './InfoTooltip.vue';
import BasePillOption from './BasePillOption.vue';
import BasePillRadio from './BasePillRadio.vue';
import BaseAccordion from './BaseAccordion.vue';

const emit = defineEmits(['update:options']);

// Descriptions from docs/design/options-coverage.md
const OPTIONS_META = {
    lang_in: { desc: "源语言代码（如 en）", default: "en" },
    lang_out: { desc: "目标语言代码（如 zh）", default: "zh" },
    pages: { desc: "指定翻译页码范围，格式如 1,2,1-,-3,3-5", default: "" },
    
    // Output & Watermark
    no_dual: { desc: "不输出双语 PDF", default: false },
    no_mono: { desc: "不输出单语 PDF", default: false },
    watermark_output_mode: { desc: "水印输出模式：watermarked / no_watermark / both", default: "no_watermark" },
    only_include_translated_page: { desc: "仅输出翻译页（仅在指定 pages 时生效）", default: false },

    // Advanced
    skip_clean: { desc: "跳过 PDF 清理步骤", default: false },
    enhance_compatibility: { desc: "兼容性增强（等同 skip_clean + dual_translate_first + disable_rich_text_translate）", default: false },
    disable_rich_text_translate: { desc: "禁用富文本翻译（提高兼容性）", default: false },
    disable_same_text_fallback: { desc: "禁用“译文等于原文时回退”逻辑", default: false },
    primary_font_family: { desc: "覆盖译文主字体族（serif / sans-serif / script）", default: null },
    add_formula_placehold_hint: { desc: "添加公式占位提示（不推荐，可能影响质量）", default: false },
    split_short_lines: { desc: "强制拆分短行（可能影响排版/稳定性）", default: false },
    short_line_split_factor: { desc: "短行拆分阈值系数（页内行长中位数 × 系数）", default: 0.8 },
    skip_scanned_detection: { desc: "跳过扫描检测（非扫描文档更快）", default: false },
    ocr_workaround: { desc: "OCR workaround（实验性，给文本加背景）", default: false },
    auto_enable_ocr_workaround: { desc: "自动启用 OCR workaround（重扫描文档）", default: false },
    auto_extract_glossary: { desc: "自动抽取术语", default: true },
    save_auto_extracted_glossary: { desc: "保存自动术语 CSV 到输出目录", default: true },
    custom_system_prompt: { desc: "自定义系统提示词", default: "" },

    // Performance & Split
    qps: { desc: "翻译服务 QPS 限制（速率）", default: 4 },
    max_pages_per_part: { desc: "分片翻译时每片最大页数（不设则不分片）", default: null },
    pool_max_workers: { desc: "内部任务池最大线程数（默认随 QPS）", default: null },
    term_pool_max_workers: { desc: "术语抽取线程池最大线程数（默认随 pool_max_workers）", default: null },

    // Phase 4 - Debug
    skip_translation: { desc: "跳过 Translate Paragraphs；同时会自动关闭术语抽取", default: false },
    only_parse_generate_pdf: { desc: "只解析并生成 PDF，不做翻译；会移除大量阶段", default: false },
};

const form = reactive({
  lang_in: 'en',
  lang_out: 'zh',
  pages: '',
  
  // Output & Watermark
  no_dual: false,
  no_mono: false,
  watermark_output_mode: 'no_watermark',
  only_include_translated_page: false,

  // Advanced defaults
  skip_clean: false,
  enhance_compatibility: false,
  disable_rich_text_translate: false,
  disable_same_text_fallback: false,
  primary_font_family: null,
  add_formula_placehold_hint: false,
  split_short_lines: false,
  short_line_split_factor: 0.8,
  skip_scanned_detection: false,
  ocr_workaround: false,
  auto_enable_ocr_workaround: false,
  auto_extract_glossary: true,
  save_auto_extracted_glossary: true,
  custom_system_prompt: '',
  
  // Performance
  qps: 4,
  max_pages_per_part: null,
  pool_max_workers: null, // Auto
  term_pool_max_workers: null, // Auto

  // Debug
  skip_translation: false,
  only_parse_generate_pdf: false,
});

// Mutual exclusion for no_dual / no_mono
watch(() => form.no_dual, (val) => {
    if (val) form.no_mono = false;
});
watch(() => form.no_mono, (val) => {
    if (val) form.no_dual = false;
});

watch(form, (newVal) => {
  // Filter out null/undefined/empty string options to avoid sending invalid values
  const cleanOptions: Record<string, any> = {};
  for (const [key, value] of Object.entries(newVal)) {
      if (value !== null && value !== undefined && value !== '') {
          cleanOptions[key] = value;
      }
  }
  emit('update:options', cleanOptions);
}, { deep: true, immediate: true });
</script>
