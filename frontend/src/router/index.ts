import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import HistoryView from '../views/HistoryView.vue';
import QueueView from '../views/QueueView.vue';
import TaskDetailView from '../views/TaskDetailView.vue';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView
        },
        {
            path: '/history',
            name: 'history',
            component: HistoryView
        },
        {
            path: '/queue',
            name: 'queue',
            component: QueueView
        },
        {
            path: '/history/:id',
            name: 'task-detail',
            component: TaskDetailView,
            props: true
        }
    ]
});

export default router;
