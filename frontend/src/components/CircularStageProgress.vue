<template>
  <div class="flex flex-col items-center justify-center p-4">
    <div class="relative" :style="{ width: size + 'px', height: size + 'px' }">
      <svg 
          class="transform -rotate-90 w-full h-full" 
          :width="size" 
          :height="size" 
          :viewBox="`0 0 ${size} ${size}`"
      >
        <!-- Case: No stages info yet -->
        <circle
            v-if="!stages || stages.length === 0"
            cx="50%" cy="50%" :r="radius"
            stroke="#e5e7eb" :stroke-width="strokeWidth" fill="transparent"
        />

        <!-- Segments -->
        <template v-else>
            <!-- Background Ring (Pending) -->
            <circle
                cx="50%" cy="50%" :r="radius"
                stroke="#f3f4f6" :stroke-width="strokeWidth" fill="transparent"
            />
            
            <!-- Render each stage segment -->
            <path
                v-for="(stage, index) in segments"
                :key="index"
                :d="stage.path"
                fill="none"
                :stroke="getStageColor(stage.status)"
                :stroke-width="strokeWidth"
                :stroke-dasharray="stage.dashArray"
                :stroke-dashoffset="0"
                class="transition-all duration-300"
                :class="{ 'opacity-50': stage.status === 'pending', 'opacity-100': stage.status !== 'pending' }"
            />
        </template>
      </svg>
      
      <!-- Center Text -->
      <div class="absolute inset-0 flex flex-col items-center justify-center text-center px-2">
          <template v-if="stages && stages.length > 0">
              <div class="text-2xl font-bold text-gray-800">
                  {{ Math.round(overallProgress) }}%
              </div>
              <div class="text-[10px] text-gray-400 uppercase tracking-wide mt-1">Total</div>
          </template>
          <template v-else>
              <div class="text-sm text-gray-400">Waiting...</div>
          </template>
      </div>
    </div>

    <!-- Below Ring: Current Stage Info -->
    <div class="mt-4 text-center max-w-[200px]">
        <div v-if="currentStageName" class="animate-fade-in">
             <h4 class="text-sm font-semibold text-gray-700 truncate" :title="currentStageName">
                 {{ formatStageName(currentStageName) }}
             </h4>
             <p class="text-xs text-blue-600 font-medium mt-0.5" v-if="status === 'running'">
                 {{ Math.round(currentStageProgress) }}%
             </p>
        </div>
        <div v-else-if="status === 'queued'" class="text-xs text-gray-500">
            Job Queued
        </div>
        <div v-else-if="status === 'idle'" class="text-xs text-gray-400">
            Ready to start
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Stage {
    name: string;
    weight: number;
    status: 'pending' | 'running' | 'completed';
    percent: number;
}

const props = withDefaults(defineProps<{
  stages: Stage[];
  currentStageName: string;
  currentStageProgress: number;
  overallProgress: number;
  status: string;
  size?: number;
  strokeWidth?: number;
}>(), {
  size: 160,
  strokeWidth: 12
});

const radius = computed(() => (props.size - props.strokeWidth) / 2);
const circumference = computed(() => 2 * Math.PI * radius.value);

// Helper to format stage names for display
const formatStageName = (name: string) => {
    // Basic cleanup: CamelCase to Space
    // e.g. "TranslateParagraphs" -> "Translate Paragraphs"
    // But backend names might be "Translate Paragraphs" directly or tokens
    // Just return as is or limit length
    return name;
};

const getStageColor = (status: string) => {
    switch (status) {
        case 'completed': return '#10b981'; // green-500
        case 'running': return '#3b82f6';   // blue-500
        default: return '#e5e7eb';          // gray-200 (should be covered by bg but good for segment)
    }
};

interface Segment {
    path: string;
    status: string;
    dashArray: string;
}

const segments = computed<Segment[]>(() => {
    if (!props.stages || props.stages.length === 0) return [];

    const totalWeight = props.stages.reduce((acc, s) => acc + s.weight, 0);
    if (totalWeight === 0) return [];

    const results: Segment[] = [];
    let startAngle = 0;

    // Use a small gap between segments for visual clarity? Maybe
    // SVG arc calculation
    
    // Logic: 
    // We want to render segments. 
    // stroke-dasharray can be used but calculating actual arcs d="M... A..." is better for precise control with gaps or strictly by weight?
    // Actually, simple way: stroke-dasharray = "portion gap"
    // portion = (weight / total) * circumference
    
    // Better visual: Use multiple circle overlays? No, they overlap start point.
    // Use path with "A" (Arc) command.
    
    const center = props.size / 2;
    const r = radius.value;

    props.stages.forEach(stage => {
        const weightShare = stage.weight / totalWeight;
        const angle = weightShare * 360;
        
        // Skip tiny segments?
        if (angle < 0.1) return;

        const endAngle = startAngle + angle;
        
        // Calculate Path
        const startRad = (startAngle - 90) * Math.PI / 180;
        const endRad = (endAngle - 90) * Math.PI / 180;
        
        const x1 = center + r * Math.cos(startRad);
        const y1 = center + r * Math.sin(startRad);
        const x2 = center + r * Math.cos(endRad);
        const y2 = center + r * Math.sin(endRad);
        
        // Large arc flag
        const largeArcFlag = angle > 180 ? 1 : 0;
        
        // Gap correction: if angle is 360, it's a circle.
        // If we want gaps, shorten endAngle slightly.
        // Let's rely on simple drawing first.
        
        let path = "";
        if (Math.abs(angle - 360) < 0.01) {
             path = `M ${center - r} ${center} A ${r} ${r} 0 1 0 ${center + r} ${center} A ${r} ${r} 0 1 0 ${center - r} ${center}`; // Full circle approximation
        } else {
             path = `M ${x1} ${y1} A ${r} ${r} 0 ${largeArcFlag} 1 ${x2} ${y2}`;
        }
        
        results.push({
            path,
            status: stage.status,
            dashArray: 'none' // managed by path d
        });

        startAngle += angle;
    });

    return results;
});

</script>
