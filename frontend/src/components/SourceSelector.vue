<template>
  <div class="space-y-4">
    <div class="flex space-x-4 border-b">
      <button 
        v-for="mode in modes" 
        :key="mode"
        class="pb-2 px-4 font-medium"
        :class="selectedMode === mode ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'"
        @click="selectedMode = mode"
      >
        {{ mode === 'platform' ? 'Platform' : 'Custom' }}
      </button>
    </div>

    <!-- Platform Dropdown -->
    <div v-if="selectedMode === 'platform'" class="space-y-2">
      <select 
         v-if="availableChannels.platform.length > 0"
         v-model="selectedChannelId"
         @change="selectPlatform(selectedChannelId)"
         class="w-full border rounded-md px-3 py-2 bg-white focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="" disabled>Select a platform</option>
        <option 
           v-for="channel in availableChannels.platform" 
           :key="channel.id" 
           :value="channel.id"
           :disabled="!channel.enabled"
        >
           {{ channel.label }} {{ !channel.enabled ? `(${channel.disabled_reason || 'disabled'})` : '' }}
        </option>
      </select>
      <div v-else class="text-sm text-gray-500">No platform channels available.</div>
      
      <p v-if="selectedChannelId" class="text-xs text-green-600 mt-1">
         Selected: {{ availableChannels.platform.find(c => c.id === selectedChannelId)?.label }}
      </p>
    </div>

    <!-- Custom List -->
    <div v-else class="space-y-4">
      <div v-if="!selectedCustomChannelId">
         <div 
           v-for="channel in availableChannels.custom" 
           :key="channel.id"
           class="p-3 border rounded-lg hover:border-blue-400 cursor-pointer flex justify-between items-center"
           @click="selectCustomChannel(channel)"
         >
           <span class="font-medium">{{ channel.label }}</span>
            <span v-if="channel.openai_compatible" class="text-xs text-gray-400 bg-gray-100 px-1 rounded">OpenAI Compatible</span>
         </div>
      </div>

       <!-- Custom Form -->
       <div v-else class="space-y-3">
         <div class="flex items-center justify-between">
           <h4 class="font-medium">{{ selectedCustomChannelLabel }}</h4>
           <button @click="resetCustomSelection" class="text-sm text-blue-600 hover:underline">Change</button>
         </div>
         
         <div v-for="field in currentCustomFields" :key="field.key">
           <label class="block text-sm font-medium text-gray-700 mb-1">
             {{ field.label }} 
             <span v-if="field.required" class="text-red-500">*</span>
           </label>
           <input 
             v-model="customFormData[field.key]"
             :type="field.secret ? 'password' : 'text'"
             class="w-full border rounded-md px-3 py-2"
           >
         </div>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { fetchChannels } from '../api';
import type { ChannelResponse, Channel, ChannelField } from '../types';

const emit = defineEmits(['update:source']);

const modes = ['platform', 'custom'] as const;
const selectedMode = ref<'platform' | 'custom'>('platform');
const availableChannels = ref<ChannelResponse>({ platform: [], custom: [], unsupported: [] });

// Selections
const selectedChannelId = ref<string>('');
const selectedCustomChannelId = ref<string>('');
const selectedCustomChannelLabel = ref<string>('');
const currentCustomFields = ref<ChannelField[]>([]);
const customFormData = ref<Record<string, any>>({});

// Initialize
onMounted(async () => {
  try {
    const res = await fetchChannels();
    availableChannels.value = res.data;
    
    // Auto-select first enabled platform channel
    const firstEnabled = availableChannels.value.platform.find(c => c.enabled);
    if (firstEnabled) {
      selectPlatform(firstEnabled.id);
    }
  } catch (e) {
    console.error('Failed to load channels', e);
  }
});

// Logic
const selectPlatform = (id: string) => {
  selectedChannelId.value = id;
  emit('update:source', { mode: 'platform', channel_id: id });
};

const selectCustomChannel = (channel: Channel) => {
  selectedCustomChannelId.value = channel.id;
  selectedCustomChannelLabel.value = channel.label;
  currentCustomFields.value = channel.fields || [];
  // Reset form data for new selection
  customFormData.value = {};
};

const resetCustomSelection = () => {
  selectedCustomChannelId.value = '';
  customFormData.value = {};
  emit('update:source', null);
};

// Watch Custom Form changes
watch(customFormData, (newVal) => {
  if (selectedMode.value === 'custom' && selectedCustomChannelId.value) {
    emit('update:source', {
      mode: 'custom',
      channel_id: selectedCustomChannelId.value,
      credentials: { ...newVal }
    });
  }
}, { deep: true });

// Watch mode switch
watch(selectedMode, () => {
  selectedChannelId.value = ''; // Reset selection on mode switch
  resetCustomSelection();
});
</script>
