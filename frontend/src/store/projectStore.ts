import { create } from 'zustand';

export interface Project {
    id: number;
    name: string;
    description: string | null;
    paper_field: string;
    color_scheme: string;
    status: string;
    created_at: string;
    document_count: number;
    prompt_count: number;
    image_count: number;
}

interface ProjectState {
    currentProject: Project | null;
    projects: Project[];
    setCurrentProject: (project: Project | null) => void;
    setProjects: (projects: Project[]) => void;
    clearState: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
    currentProject: null,
    projects: [],
    setCurrentProject: (project) => set({ currentProject: project }),
    setProjects: (projects) => set({ projects }),
    clearState: () => set({ currentProject: null, projects: [] })
}));
