export interface Job {
    job_id: string;
    status: 'queued' | 'running' | 'finished' | 'failed' | 'canceled';
    created_at: string;
    folder_name?: string;
    display_name?: string;
    original_filename?: string;
    renamed_at?: string;
    has_mono?: boolean;
    has_dual?: boolean;
}

export interface ChannelField {
    key: string;
    label: string;
    required: boolean;
    secret: boolean;
}

export interface Channel {
    id: string;
    label: string;
    enabled?: boolean;
    disabled_reason?: string;
    visible?: boolean;
    openai_compatible?: boolean;
    fields?: ChannelField[];
    reason?: string; // for unsupported
}

export interface ChannelResponse {
    platform: Channel[];
    custom: Channel[];
    unsupported: Channel[];
}

export interface JobFile {
    file_id: string;
    type: 'original' | 'mono' | 'dual' | string;
    watermark: string;
    filename: string;
    size: number;
    url: string;
}

export interface QueueResponse {
    max_running: number;
    running: string[];
    queued: string[];
}
