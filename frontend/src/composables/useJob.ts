import { ref, reactive } from 'vue';
import { createJob, fetchJobFiles, cancelJob, runJob } from '../api';
import type { JobFile } from '../types';

export function useJob() {
    const job = reactive({
        id: '',
        status: 'idle', // idle | queued | running | finished | failed | canceled
        overallProgress: 0,
        stageName: '',
        stageProgress: 0,
        error: '',
        info: '',
        stages: [] as Array<{ name: string; weight: number; status: 'pending' | 'running' | 'completed'; percent: number }>
    });

    const files = ref<JobFile[]>([]);
    let eventSource: EventSource | null = null;
    let lastUpdate = 0;

    const reset = () => {
        job.id = '';
        job.status = 'idle';
        job.overallProgress = 0;
        job.stageName = '';
        job.stageProgress = 0;
        job.error = '';
        job.info = '';
        job.stages = [];
        files.value = [];
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    };

    const startJob = async (file: File, options: any, source: any) => {
        reset();
        try {
            const formData = new FormData();
            formData.append('file', file);
            // Critical: Ensure these are JSON strings per contract
            formData.append('options', JSON.stringify(options));
            // Handle source: if platform, just {mode: platform, channel_id: ...}, if custom includes credentials
            formData.append('source', JSON.stringify(source));

            const res = await createJob(formData);
            job.id = res.data.job_id;
            // Status might be 'queued' initially
            job.status = res.data.status || 'queued';

            // Explicitly run the job as per new requirement
            try {
                const runRes = await runJob(job.id);
                job.status = runRes.data.status;
            } catch (e: any) {
                console.error('Failed to run job immediate', e);
                // If run fails, we might want to surface it, but connectSSE might catch generic errors too.
                // For now just log, as user request didn't specify error handling for runJob specifically other than flow.
            }

            connectSSE(job.id);
        } catch (e: any) {
            job.status = 'failed';
            job.error = e.response?.data?.detail || e.message || 'Failed to create job';
        }
    };

    const connectSSE = (id: string) => {
        if (eventSource) eventSource.close();

        eventSource = new EventSource(`/api/jobs/${id}/events`);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleEvent(data);
            } catch (e) {
                console.error('SSE Parse Error', e);
            }
        };

        eventSource.onerror = (e) => {
            console.error('SSE Error', e);
            // Wait a bit and check status via API or just show error?
            // Contract says "heartbeat", so if connection dies we might want to alert
            // For MVP, if it's finished we are good, otherwise alert
            if (!['finished', 'failed', 'canceled'].includes(job.status)) {
                // Optional: retry logic or status check
                job.info = 'Connection loop... checking status...';
            }
        };
    };

    const handleEvent = (payload: any) => {
        // Throttle UI updates if needed (rAF pattern)
        // For simplicity, we just update state reactive props which Vue batches fairly well
        // But we can limit frequency if super high throughput
        const now = Date.now();
        if (payload.type === 'progress_update' && now - lastUpdate < 100) {
            return; // Skip if too fast < 100ms
        }
        lastUpdate = now;

        // Fixed Types: stage_summary | progress_start | progress_update | progress_end | finish | error | heartbeat
        switch (payload.type) {
            case 'stage_summary':
                if (payload.data && Array.isArray(payload.data.stages)) {
                    // Populate stages from summary
                    job.stages = payload.data.stages.map((s: any) => ({
                        name: s.name,
                        weight: s.weight ?? s.percent, // Backend might send 'percent' (0-100) as weight share
                        status: 'pending',
                        percent: 0
                    }));
                }
                job.status = 'running';
                break;
            case 'progress_start':
                job.status = 'running';
                if (payload.data.stage) {
                    job.stageName = payload.data.stage;
                    // Mark previous stages as completed, current as running
                    if (job.stages.length > 0) {
                        let foundCurrent = false;
                        for (const s of job.stages) {
                            if (s.name === payload.data.stage) {
                                s.status = 'running';
                                foundCurrent = true;
                            } else if (!foundCurrent) {
                                s.status = 'completed';
                                s.percent = 100;
                            }
                        }
                    }
                }
                break;
            case 'progress_update':
                job.status = 'running';
                job.overallProgress = payload.data.overall_progress || job.overallProgress;
                job.stageName = payload.data.stage || job.stageName;
                job.stageProgress = payload.data.stage_progress || 0;

                // Update stage in list
                if (job.stages.length > 0 && job.stageName) {
                    const currentStage = job.stages.find(s => s.name === job.stageName);
                    if (currentStage) {
                        currentStage.status = 'running';
                        currentStage.percent = job.stageProgress;
                    }
                }
                break;
            case 'finish':
                job.status = 'finished';
                job.overallProgress = 100;
                job.stageProgress = 100;
                // Mark all stages as completed
                if (job.stages.length > 0) {
                    job.stages.forEach(s => {
                        s.status = 'completed';
                        s.percent = 100;
                    });
                }
                if (eventSource) eventSource.close();
                loadFiles(job.id);
                break;
            case 'error':
                job.status = 'failed';
                job.error = payload.data.error || payload.data.message || 'Unknown error';
                if (eventSource) eventSource.close();
                break;
        }
    };

    const loadFiles = async (id: string) => {
        try {
            const res = await fetchJobFiles(id);
            files.value = res.data;
        } catch (e) {
            console.error('Failed to load files', e);
        }
    };

    const doCancel = async () => {
        if (!job.id) return;
        try {
            await cancelJob(job.id);
            job.status = 'canceled';
            if (eventSource) eventSource.close();
        } catch (e) {
            alert('Failed to cancel');
        }
    };

    return {
        job,
        files,
        startJob,
        cancel: doCancel,
        reset
    };
}
