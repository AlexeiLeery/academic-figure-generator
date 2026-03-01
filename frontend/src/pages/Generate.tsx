import { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Loader2, Wand2, Image as ImageIcon, Download } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/api';

export function Generate() {
   const { user } = useAuthStore();
   const [prompt, setPrompt] = useState('');
   // const [resolution, setResolution] = useState('2K');
   const [aspectRatio, setAspectRatio] = useState('16:9');
   const [isGenerating, setIsGenerating] = useState(false);
   const [resultImage, setResultImage] = useState<{ url: string; status: 'pending' | 'completed' | 'failed' } | null>(null);

   const handleGenerate = async () => {
      if (!prompt.trim() || !user) return;
      setIsGenerating(true);
      setResultImage({ url: '', status: 'pending' });

      try {
         // Direct generation without project/document context
         await api.post('/images/generate-direct', {
            prompt,
            // resolution,
            aspect_ratio: aspectRatio,
         });
         // In a real app with SSE, we'd setup a listener here.
         // Mocking a successful response for now.
         setTimeout(() => {
            setResultImage({
               url: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop', // Placeholder abstract image
               status: 'completed'
            });
            setIsGenerating(false);
         }, 5000);
      } catch (e) {
         console.error(e);
         setResultImage({ url: '', status: 'failed' });
         setIsGenerating(false);
      }
   };

   return (
      <div className="max-w-4xl mx-auto space-y-6">
         <div>
            <h1 className="text-3xl font-bold tracking-tight">直接生成模式</h1>
            <p className="text-muted-foreground mt-1">跳过文档解析环节，直接输入您的需求即刻生成学术配图。</p>
         </div>

         <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-6">
               <Card>
                  <CardHeader>
                     <CardTitle>配图描述</CardTitle>
                     <CardDescription>用文字详细描述您想要生成的论文配图。</CardDescription>
                  </CardHeader>
                  <CardContent>
                     <Textarea
                        placeholder="例如：绘制一个基于Transformer的跨模态融合架构图。包含两个分支：视觉编码器和文本编码器，它们在中间层通过自注意力机制进行跨模态交互，最后输出分类结果..."
                        className="min-h-[200px]"
                        value={prompt}
                        onChange={e => setPrompt(e.target.value)}
                     />
                  </CardContent>
                  <CardFooter className="flex justify-between border-t p-4">
                     <Select value={aspectRatio} onValueChange={setAspectRatio}>
                        <SelectTrigger className="w-[120px]">
                           <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                           <SelectItem value="16:9">16:9 宽屏</SelectItem>
                           <SelectItem value="4:3">4:3 标准</SelectItem>
                           <SelectItem value="1:1">1:1 方形</SelectItem>
                        </SelectContent>
                     </Select>
                     <Button onClick={handleGenerate} disabled={isGenerating || !prompt.trim()}>
                        {isGenerating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Wand2 className="w-4 h-4 mr-2" />}
                        {isGenerating ? '生成中...' : '生成配图'}
                     </Button>
                  </CardFooter>
               </Card>
            </div>

            <div className="space-y-6">
               <Card className="h-full min-h-[400px] flex flex-col">
                  <CardHeader>
                     <CardTitle>生成预览</CardTitle>
                     <CardDescription>您生成的配图将在此处显示。</CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1 flex items-center justify-center p-6 bg-muted/10 border-t">
                     {isGenerating ? (
                        <div className="text-center">
                           <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
                           <p className="text-sm text-muted-foreground mt-4">AI 正在努力绘制中，请耐心等待...</p>
                        </div>
                     ) : resultImage?.status === 'completed' && resultImage.url ? (
                        <img src={resultImage.url} alt="Generated result" className="rounded shadow-md max-h-full max-w-full object-contain" />
                     ) : (
                        <div className="text-center">
                           <ImageIcon className="h-12 w-12 text-muted-foreground/50 mx-auto" />
                           <p className="text-sm text-muted-foreground mt-4">暂无生成的图片内容</p>
                        </div>
                     )}
                  </CardContent>
                  {resultImage?.status === 'completed' && resultImage.url && (
                     <CardFooter className="bg-muted/30 pt-4 border-t flex justify-end">
                        <Button variant="secondary">
                           <Download className="w-4 h-4 mr-2" />
                           下载高清原图
                        </Button>
                     </CardFooter>
                  )}
               </Card>
            </div>
         </div>
      </div>
   );
}
