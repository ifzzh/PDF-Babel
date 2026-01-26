import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    timeout: 60000,
});

export default api;

// API Methods
export const fetchChannels = () => api.get('/channels');
export const createJob = (formData: FormData) => api.post('/jobs', formData, {
    headers: {
        'Content-Type': 'multipart/form-data',
    },
});
export const fetchJobs = (params?: any) => api.get('/jobs', { params });
export const fetchJob = (id: string) => api.get(`/jobs/${id}`);
export const fetchJobFiles = (id: string) => api.get(`/jobs/${id}/files`);
export const cancelJob = (id: string) => api.post(`/jobs/${id}/cancel`);
export const fetchQueue = () => api.get('/queue');
export const resumeQueue = (data: { mode?: string; job_ids?: string[] }) => api.post('/queue/resume', data);

// Rename interface
export const renameJob = (id: string, data: {
    folder_name?: string;
    original_filename?: string;
    confirm?: boolean
}) => api.patch(`/jobs/${id}`, data);

export const runJob = (id: string) => api.post(`/jobs/${id}/run`);
export const deleteJob = (id: string, confirm: boolean = false) => api.delete(`/jobs/${id}`, { params: { confirm } });
export const deleteJobs = (data: { job_ids: string[], confirm: boolean }) => api.post('/jobs/delete', data);
