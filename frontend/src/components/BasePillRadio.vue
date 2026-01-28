<template>
  <button 
    type="button" 
    class="relative inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all duration-200 select-none group"
    :class="[
      modelValue === value
        ? 'bg-blue-100 text-blue-700 border-blue-300 shadow-sm' 
        : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
    ]"
    @click="select"
  >
    <span>{{ label }}</span>
    
    <!-- Tooltip -->
    <div 
      v-if="desc"
      class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1.5 text-xs text-white bg-gray-800 rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none z-[100] w-max max-w-[200px] text-center normal-case font-normal leading-relaxed"
    >
      {{ desc }}
      <!-- Arrow -->
      <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
    </div>
  </button>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: string | number | boolean;
  value: string | number | boolean;
  label: string;
  desc?: string;
}>();

const emit = defineEmits(['update:modelValue']);

const select = () => {
  emit('update:modelValue', props.value);
};
</script>
