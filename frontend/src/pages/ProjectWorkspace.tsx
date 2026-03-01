import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileUp, FileText, Image as ImageIcon, Send, RefreshCw, Download } from 'lucide-react';

import { api } from '../lib/api';
import { useProjectStore } from '../store/projectStore';
import { fetchAuthedBlob, triggerBrowserDownload } from '../lib/blob';
import { useAuthStore } from '../store/authStore';

import { Button } from '../components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

type DocumentItem = {
    id: string;
    original_filename: string;
    file_type: string;
    file_size_bytes: number;
    parse_status: 'pending' | 'parsing' | 'completed' | 'failed' | string;
    parse_error?: string | null;
    sections?: Array<{ title?: string; content?: string }> | null;
    created_at?: string;
};

export function ProjectWorkspace() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { currentProject, setCurrentProject } = useProjectStore();
    const token = useAuthStore((s) => s.token);

    const [isLoading, setIsLoading] = useState(true);
    const [documents, setDocuments] = useState<DocumentItem[]>([]);
    const [prompts, setPrompts] = useState<any[]>([]);
    const [images, setImages] = useState<any[]>([]);
    const [activeTab, setActiveTab] = useState('prompts');

    // Upload state
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    // Prompt Generation state
    const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false);
    const [isDownloading, setIsDownloading] = useState<string | null>(null);
    const [isPreviewing, setIsPreviewing] = useState<Record<string, boolean>>({});
    const [imagePreviews, setImagePreviews] = useState<Record<string, string>>({});
    const previewUrlsRef = useRef<Record<string, string>>({});
    const [promptMode, setPromptMode] = useState<'overall' | 'sections'>('overall');
    const [promptRequest, setPromptRequest] = useState('');
    const [selectedSectionIndices, setSelectedSectionIndices] = useState<number[]>([]);

    useEffect(() => {
        if (id && token) {
            fetchProjectData(id);
        }
        return () => setCurrentProject(null);
    }, [id, token]);

    useEffect(() => {
        return () => {
            // Revoke any blob: URLs we created to avoid memory leaks.
            for (const url of Object.values(previewUrlsRef.current)) {
                try {
                    URL.revokeObjectURL(url);
                } catch {
                    // ignore
                }
            }
            previewUrlsRef.current = {};
        };
    }, []);

    const fetchProjectData = async (projectId: string) => {
        setIsLoading(true);
        try {
            const projRes = await api.get(`/projects/${projectId}`);
            setCurrentProject(projRes.data);

            try {
                const docsRes = await api.get(`/projects/${projectId}/documents`);
                const nextDocs = docsRes.data || [];
                setDocuments(nextDocs);
                const firstParsed = nextDocs.find(
                    (d: any) => d.parse_status === 'completed' && Array.isArray(d.sections) && d.sections.length > 0
                );
                if (firstParsed?.sections?.length && selectedSectionIndices.length === 0) {
                    setSelectedSectionIndices(firstParsed.sections.map((_: any, idx: number) => idx));
                }
            } catch (e) {
                console.debug('Failed to fetch documents', e);
                setDocuments([]);
            }

            try {
                const promptsRes = await api.get(`/projects/${projectId}/prompts`);
                setPrompts(promptsRes.data);
            } catch (e) {
                console.debug('Failed to fetch prompts', e);
            }

            try {
                const imagesRes = await api.get(`/projects/${projectId}/images`);
                setImages(imagesRes.data);
            } catch (e) {
                console.debug('Failed to fetch images', e);
            }

        } catch (err) {
            console.error(err);
            navigate('/projects');
        } finally {
            setIsLoading(false);
        }
    };

    const ensureImagePreview = useCallback(async (imageId: string) => {
        if (imagePreviews[imageId]) return;
        if (isPreviewing[imageId]) return;

        setIsPreviewing(prev => ({ ...prev, [imageId]: true }));
        try {
            const { blob } = await fetchAuthedBlob(`/images/${imageId}/download`);
            const url = URL.createObjectURL(blob);

            // Revoke old one if exists
            const old = previewUrlsRef.current[imageId];
            if (old) {
                try {
                    URL.revokeObjectURL(old);
                } catch {
                    // ignore
                }
            }
            previewUrlsRef.current[imageId] = url;
            setImagePreviews(prev => ({ ...prev, [imageId]: url }));
        } catch (err) {
            console.error('Preview fetch failed', err);
        } finally {
            setIsPreviewing(prev => ({ ...prev, [imageId]: false }));
        }
    }, [imagePreviews, isPreviewing]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !id) return;

        setIsUploading(true);
        setUploadProgress(0);
        const formData = new FormData();
        formData.append('file', file);

        try {
            await api.post(`/projects/${id}/documents`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: (evt) => {
                    const total = evt.total || 0;
                    if (!total) return;
                    setUploadProgress(Math.min(100, Math.round((evt.loaded / total) * 100)));
                },
            });
            // Refresh docs
            await fetchProjectData(id);
            alert('文件上传成功，已加入解析队列。');
        } catch (err: any) {
            console.error('File upload failed', err);
            const detail = err?.response?.data?.detail;
            alert(detail ? `文件上传失败：${detail}` : '文件上传失败，请检查后端/存储服务是否正常。');
        } finally {
            setIsUploading(false);
            setUploadProgress(0);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDownloadImage = async (imageId: string) => {
        try {
            setIsDownloading(imageId);
            const { blob, ext } = await fetchAuthedBlob(`/images/${imageId}/download`);
            triggerBrowserDownload(blob, `academic-figure-${imageId}.${ext}`);
        } catch (err: any) {
            console.error('Download failed', err);
            const detail = err?.response?.data?.detail;
            alert(detail ? `下载失败：${detail}` : '下载失败，请稍后重试。');
        } finally {
            setIsDownloading(null);
        }
    };

    /*
    const handleGeneratePrompts = async () => {
        if (!id) return;
        setIsGeneratingPrompt(true);
        try {
            await api.post(`/projects/${id}/prompts/generate`, {
                section_indices: selectedDocIds,
                form_data: {} // custom params based on spec
            });
            fetchProjectData(id);
        } catch (err) {
            console.error('Failed to generate prompts', err);
        } finally {
            setTimeout(() => {
                setIsGeneratingPrompt(false);
                // 提示此为演示由于需要SSE
                setPrompts((prev: any[]) => [...prev, {
                    id: 'demo-p-1',
                    content: '一个关于 Transformer 架构的高质量 3D 架构图，展示自注意力机制，采用 Okabe-Ito 配色，纯白背景，矢量风格。',
                    status: 'completed',
                    image_count: 0,
                    title: 'Transformer 架构图',
                    suggested_type: '架构图'
                }]);
            }, 2000);
        }
    };
    */

    const handleGeneratePrompt = async () => {
        if (!id) return;

        const parsedDoc = documents.find((d) => d.parse_status === 'completed' && Array.isArray(d.sections) && d.sections.length > 0);
        if (!parsedDoc) {
            alert('请先上传文档并等待解析完成，再生成提示词。');
            return;
        }

        if (promptMode === 'sections' && selectedSectionIndices.length === 0) {
            alert('请至少选择一个章节。');
            return;
        }

        setIsGeneratingPrompt(true);
        try {
            const beforeCount = prompts.length;
            const payload: any = {
                section_indices: selectedSectionIndices.length ? selectedSectionIndices : null,
                color_scheme: currentProject?.color_scheme || 'okabe-ito',
                figure_types: promptMode === 'overall' ? ['overall_framework'] : null,
                user_request: promptRequest.trim() ? promptRequest.trim() : null,
                max_figures: promptMode === 'overall' ? 1 : null,
            };

            await api.post(`/projects/${id}/prompts/generate`, payload);
            setActiveTab('prompts');

            // Poll prompt list until new prompts appear (simple UX)
            const deadline = Date.now() + 90_000; // 90s
            while (Date.now() < deadline) {
                await new Promise((r) => setTimeout(r, 2000));
                const promptsRes = await api.get(`/projects/${id}/prompts`);
                const next = promptsRes.data || [];
                setPrompts(next);
                if (next.length > beforeCount) break;
            }
        } catch (err: any) {
            console.error('Failed to generate prompt', err);
            const detail = err?.response?.data?.detail;
            alert(detail ? `生成提示词失败：${detail}` : '生成提示词失败，请稍后重试。');
        } finally {
            setIsGeneratingPrompt(false);
        }
    };

    const handleGenerateImage = async (promptId: string) => {
        if (!id) return;
        try {
            await api.post(`/prompts/${promptId}/images/generate`, {
                resolution: "2K",
                aspect_ratio: "16:9",
            });
            await fetchProjectData(id);
            setActiveTab('images');
        } catch (err) {
            console.error('Failed to generate image', err);
            alert('生成图像失败，请稍后重试。');
        }
    };

    if (isLoading) return <div className="p-8">加载中...</div>;
    if (!currentProject) return <div className="p-8">找不到该项目...</div>;

    return (
        <div className="h-[calc(100vh-6rem)] flex gap-6 overflow-hidden">

            {/* Left Column: Documents */}
            <Card className="w-1/3 flex flex-col h-full border-r shadow-none">
                <CardHeader className="bg-muted/30 border-b py-4">
                    <CardTitle className="text-lg flex items-center">
                        <FileText className="w-5 h-5 mr-2 text-primary" />
                        参考文档
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-hidden p-0 flex flex-col">

                    {/* Prompt intent */}
                    <div className="p-4 border-b bg-background">
                        <div className="text-sm font-medium text-muted-foreground mb-2">你想生成什么图？（可选）</div>
                        <Textarea
                            value={promptRequest}
                            onChange={(e) => setPromptRequest(e.target.value)}
                            placeholder="例如：只生成一张整体架构图（包含输入、编码器、融合模块、输出），突出本文主要贡献点。"
                            className="min-h-[90px]"
                        />
                        <div className="flex items-center justify-between gap-2 mt-3">
                            <div className="text-sm font-medium text-muted-foreground">生成方式</div>
                            <Select value={promptMode} onValueChange={(v) => setPromptMode(v as any)}>
                                <SelectTrigger className="w-[180px]">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="overall">整体架构图（1条）</SelectItem>
                                    <SelectItem value="sections">按章节生成（多条）</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                            <p className="text-xs text-muted-foreground mt-2">
                                “整体架构图”只生成 1 条提示词；“按章节生成”会基于所选章节生成多条提示词。章节勾选对两种方式都生效（用于限定参考范围）。
                            </p>
                        </div>

                    {/* Upload Area */}
                    <div className="p-4 border-b">
                        <div
                            className="border-2 border-dashed rounded-lg p-6 text-center hover:bg-muted/50 transition-colors cursor-pointer"
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input type="file" ref={fileInputRef} className="hidden" accept=".pdf,.docx,.txt" onChange={handleFileUpload} />
                            <FileUp className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                            <p className="text-sm font-medium">点击或拖拽以上传</p>
                            <p className="text-xs text-muted-foreground mt-1">支持 PDF, DOCX, TXT (最大 50MB)</p>
                        </div>

                        {isUploading && (
                            <div className="mt-4 space-y-2">
                                <div className="flex justify-between text-xs">
                                    <span>上传中...</span>
                                    <span>{uploadProgress}%</span>
                                </div>
                                <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                                    <div className="bg-primary h-full transition-all" style={{ width: `${uploadProgress}%` }} />
                                </div>
                            </div>
                        )}
                    </div>
                    {/* Document Content / Parsed Chapters */}
                    <ScrollArea className="flex-1 p-4">
                        <div className="space-y-4">
                            <div className="text-sm font-medium text-muted-foreground mb-2">已上传文档</div>
                            {documents.length === 0 ? (
                                <div className="text-sm text-muted-foreground">暂无文档，请先上传 PDF / DOCX / TXT。</div>
                            ) : (
                                <div className="space-y-2">
                                    {documents.map((doc) => (
                                        <div key={doc.id} className="flex items-start justify-between gap-2 p-3 bg-muted/20 rounded border">
                                            <div className="min-w-0">
                                                <p className="text-sm font-medium truncate">{doc.original_filename}</p>
                                                {doc.parse_status === 'failed' && doc.parse_error && (
                                                    <p className="text-xs text-destructive mt-1 line-clamp-2">{doc.parse_error}</p>
                                                )}
                                            </div>
                                            <Badge variant={doc.parse_status === 'completed' ? 'secondary' : doc.parse_status === 'failed' ? 'destructive' : 'outline'}>
                                                {doc.parse_status}
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div className="text-sm font-medium text-muted-foreground mt-6">已解析结构</div>
                            {(() => {
                                const parsedDoc = documents.find((d) => d.parse_status === 'completed' && Array.isArray(d.sections) && d.sections.length > 0);
                                if (!parsedDoc) return <div className="text-sm text-muted-foreground">上传文档并等待解析完成后，这里会显示章节结构。</div>;

                                return (
                                    <div className="space-y-2">
                                        {(parsedDoc.sections || []).map((sec, idx) => (
                                            <div key={idx} className="flex items-start space-x-2 p-3 bg-muted/40 rounded border">
                                                <input
                                                    type="checkbox"
                                                    className="mt-1"
                                                    checked={selectedSectionIndices.includes(idx)}
                                                    onChange={(e) => {
                                                        const checked = e.target.checked;
                                                        setSelectedSectionIndices((prev) => {
                                                            const set = new Set(prev);
                                                            if (checked) set.add(idx);
                                                            else set.delete(idx);
                                                            return Array.from(set).sort((a, b) => a - b);
                                                        });
                                                    }}
                                                />
                                                <div className="min-w-0">
                                                    <p className="text-sm font-medium leading-none truncate">{sec.title || `Section ${idx + 1}`}</p>
                                                    {sec.content && (
                                                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{sec.content}</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                );
                            })()}
                        </div>
                    </ScrollArea>
                </CardContent>
                <CardFooter className="p-4 border-t bg-muted/10">
                    <Button className="w-full font-semibold" onClick={handleGeneratePrompt} disabled={isGeneratingPrompt}>
                        {isGeneratingPrompt ? (
                            <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> 生成提示词中...</>
                        ) : (
                            <><Send className="w-4 h-4 mr-2" /> 生成提示词</>
                        )}
                    </Button>
                </CardFooter>
            </Card>

            {/* Right Column: Prompts & Images Tabs */}
            <Card className="flex-1 flex flex-col h-full shadow-none border-0 bg-transparent">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
                    <TabsList className="w-full justify-start rounded-none border-b bg-transparent h-14 p-0 px-4">
                        <TabsTrigger value="prompts" className="data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-full px-6">
                            提示词 ({prompts.length})
                        </TabsTrigger>
                        <TabsTrigger value="images" className="data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-full px-6">
                            生成的配图
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="prompts" className="flex-1 overflow-hidden m-0 p-4">
                        <div className="h-full flex flex-col gap-4">
                            {prompts.length === 0 ? (
                                <div className="text-center text-muted-foreground mt-20">暂无提示词生成。</div>
                            ) : (
                                <ScrollArea className="flex-1">
                                    <div className="grid gap-4">
                                        {prompts.map(prompt => (
                                            <Card key={prompt.id}>
                                                <CardHeader className="pb-2">
                                                    <div className="flex justify-between">
                                                        <CardTitle className="text-lg">
                                                            图表: {prompt.title || `Figure ${prompt.figure_number ?? ''}`}
                                                        </CardTitle>
                                                        <Badge>{prompt.suggested_figure_type || '未分类'}</Badge>
                                                    </div>
                                                </CardHeader>
                                                <CardContent>
                                                    <p className="text-sm text-muted-foreground font-mono bg-muted p-3 rounded-md max-h-32 overflow-y-auto">
                                                        {prompt.active_prompt || prompt.original_prompt || ''}
                                                    </p>
                                                </CardContent>
                                                <CardFooter className="justify-end pt-0 mt-4 border-t pt-4">
                                                    <Button size="sm" onClick={() => handleGenerateImage(prompt.id)}>
                                                        <ImageIcon className="mr-2 h-4 w-4" />
                                                        生成图像
                                                    </Button>
                                                </CardFooter>
                                            </Card>
                                        ))}
                                    </div>
                                </ScrollArea>
                            )}
                        </div>
                    </TabsContent>

                    <TabsContent value="images" className="flex-1 overflow-hidden m-0 p-4">
                        <ScrollArea className="h-full">
                            {images.length === 0 ? (
                                <div className="text-center text-muted-foreground mt-20">暂无图表生成。</div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {images.map(img => (
                                        <Card key={img.id} className="overflow-hidden">
                                            <div className="aspect-video bg-muted relative">
                                                {img.generation_status === 'completed' && imagePreviews[img.id] ? (
                                                    <img
                                                        src={imagePreviews[img.id]}
                                                        alt="Generated Figure"
                                                        className="w-full h-full object-cover"
                                                        onError={() => {
                                                            // If blob URL is revoked/invalid, allow re-fetch.
                                                            setImagePreviews(prev => {
                                                                const next = { ...prev };
                                                                delete next[img.id];
                                                                return next;
                                                            });
                                                        }}
                                                    />
                                                ) : img.generation_status === 'completed' ? (
                                                    <div className="absolute inset-0 flex items-center justify-center flex-col gap-2">
                                                        <ImageIcon className="h-8 w-8 text-muted-foreground" />
                                                        <Button
                                                            size="sm"
                                                            variant="secondary"
                                                            disabled={!!isPreviewing[img.id]}
                                                            onClick={() => ensureImagePreview(img.id)}
                                                        >
                                                            {isPreviewing[img.id] ? '加载中...' : '预览'}
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <div className="absolute inset-0 flex items-center justify-center flex-col">
                                                        {img.generation_status === 'processing' ? <RefreshCw className="h-8 w-8 animate-spin text-primary" /> : <ImageIcon className="h-8 w-8 text-muted-foreground" />}
                                                        <span className="mt-2 text-sm font-medium">{img.generation_status}</span>
                                                    </div>
                                                )}
                                            </div>
                                            <CardFooter className="p-3 bg-muted/20 flex justify-between">
                                                <span className="text-xs text-muted-foreground">{img.resolution}</span>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    disabled={img.generation_status !== 'completed' || isDownloading === img.id}
                                                    onClick={() => handleDownloadImage(img.id)}
                                                >
                                                    <Download className="h-4 w-4" />
                                                </Button>
                                            </CardFooter>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </ScrollArea>
                    </TabsContent>
                </Tabs>
            </Card>
        </div>
    );
}
