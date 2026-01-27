<template>
  <div class="flex flex-col h-full bg-white rounded-lg shadow-sm overflow-hidden">
    <!-- Header: Search -->
    <div class="p-4 border-b bg-gray-50 flex items-center justify-between gap-4">
        <h3 class="font-medium text-gray-700 hidden sm:block">Glossary Viewer</h3>
        <div class="relative flex-1 max-w-md">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="Search terms (space separated)..." 
                class="w-full pl-9 pr-4 py-2 text-sm border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
        </div>
        <div class="text-xs text-gray-500 whitespace-nowrap">
            {{ filteredRows.length }} terms
        </div>
    </div>

    <!-- Loading / Error / Empty States -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-gray-500">
        <div class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mr-2"></div>
        Loading terms...
    </div>
    
    <div v-else-if="error" class="flex-1 flex items-center justify-center text-red-500 p-8 text-center">
        <p>{{ error }}</p>
    </div>

    <div v-else-if="allRows.length === 0" class="flex-1 flex items-center justify-center text-gray-400 p-8">
        No terms found in this file.
    </div>

    <!-- Data Table -->
    <div v-else class="flex-1 overflow-auto relative">
        <table class="w-full text-sm text-left">
            <thead class="bg-gray-50 text-gray-600 font-medium sticky top-0 z-10 shadow-sm">
                <tr>
                    <th class="px-6 py-3 border-b w-1/2">Source</th>
                    <th class="px-6 py-3 border-b w-1/2">Target</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
                <tr v-if="filteredRows.length === 0">
                    <td colspan="2" class="px-6 py-8 text-center text-gray-400">
                        No matches found for "{{ searchQuery }}"
                    </td>
                </tr>
                <tr v-for="(row, idx) in paginatedRows" :key="idx" class="hover:bg-blue-50/50 transition-colors">
                    <td class="px-6 py-3 font-mono text-gray-800 select-all">{{ row.source }}</td>
                    <td class="px-6 py-3 font-mono text-gray-800 select-all">{{ row.target }}</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="border-t p-3 flex items-center justify-between bg-gray-50">
        <button 
           @click="page > 1 && page--" 
           :disabled="page <= 1"
           class="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
           <ChevronLeft class="w-4 h-4" />
        </button>
        <span class="text-xs text-gray-600 font-medium">
            Page {{ page }} of {{ totalPages }}
        </span>
        <button 
           @click="page < totalPages && page++" 
           :disabled="page >= totalPages"
           class="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
           <ChevronRight class="w-4 h-4" />
        </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Search, ChevronLeft, ChevronRight } from 'lucide-vue-next';
import Papa from 'papaparse';
import axios from 'axios';
import type { JobFile } from '../types';

const props = defineProps<{
    file: JobFile | null;
}>();

interface TermRow {
    source: string;
    target: string;
}

const loading = ref(false);
const error = ref('');
const allRows = ref<TermRow[]>([]);
const searchQuery = ref('');
const page = ref(1);
const pageSize = 50;

// Need to handle potential header variations if any, but standard is Source,Target usually?
// Actually backend produces specific CSV. Assuming no headers or standard headers.
// If headers exist, PapaParse { header: true } is good.
// Let's assume content is straightforward. 
// Standard format from `AutomaticTermExtractor` usually outputs CSV.

const loadCsv = async () => {
    if (!props.file) {
        allRows.value = [];
        return;
    }
    
    loading.value = true;
    error.value = '';
    searchQuery.value = '';
    page.value = 1;

    try {
        const res = await axios.get(props.file.url, { responseType: 'blob' });
        // Use FileReader or just text
        const text = await res.data.text();
        
        Papa.parse(text, {
            header: true, // Assuming headers like "Source", "Target" or similar
            skipEmptyLines: true,
            complete: (results) => {
                // Normalize data
                // Expect columns: source, target (case insensitive checks)
                if (results.data && results.data.length > 0) {
                     // Try to find source/target keys
                     const first = results.data[0] as any;
                     const keys = Object.keys(first);
                     // If headers are roughly "Source" and "Target"
                     // Or just take index 0 and 1 if standard
                     
                     // Fallback if header detection fails (e.g. no header row in some cases?)
                     // But backend doc says standard CSV with headers usually.
                     // Let's assume standard "source", "target" or similar columns.
                     
                     const srcKey = keys.find(k => k.toLowerCase().includes('source') || k.toLowerCase().includes('original')) || keys[0];
                     const tgtKey = keys.find(k => k.toLowerCase().includes('target') || k.toLowerCase().includes('translation')) || keys[1];

                     allRows.value = results.data.map((row: any) => ({
                         source: row[srcKey] || '',
                         target: row[tgtKey] || ''
                     })).filter(r => r.source || r.target);
                } else {
                    allRows.value = [];
                }
                loading.value = false;
            },
            error: (err) => {
                error.value = 'Failed to parse CSV: ' + err.message;
                loading.value = false;
            }
        });
    } catch (e: any) {
        error.value = 'Failed to load file: ' + e.message;
        loading.value = false;
    }
};

watch(() => props.file, loadCsv, { immediate: true });

// Filter logic
const filteredRows = computed(() => {
    if (!searchQuery.value.trim()) return allRows.value;
    
    const terms = searchQuery.value.toLowerCase().split(/\s+/).filter(Boolean);
    return allRows.value.filter(row => {
        const s = row.source.toLowerCase();
        const t = row.target.toLowerCase();
        // AND logic: all terms must appear in either source or target (combined)
        return terms.every(term => s.includes(term) || t.includes(term));
    });
});

// Reset page on search
watch(searchQuery, () => page.value = 1);

// Pagination
const totalPages = computed(() => Math.ceil(filteredRows.value.length / pageSize));
const paginatedRows = computed(() => {
    const start = (page.value - 1) * pageSize;
    return filteredRows.value.slice(start, start + pageSize);
});

</script>
