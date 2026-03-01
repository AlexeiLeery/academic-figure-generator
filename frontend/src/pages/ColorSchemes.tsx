import { useEffect, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

export interface ColorScheme {
    id: string;
    user_id?: string | null;
    name: string;
    type?: 'preset' | 'custom' | string;
    is_default?: boolean;
    created_at?: string;
    colors: {
        primary: string;
        secondary: string;
        tertiary: string;
        text: string;
        fill: string;
        section_bg: string;
        border: string;
        arrow: string;
    };
}

const FALLBACK_PRESETS: ColorScheme[] = [
    {
        id: 'preset-okabe-ito',
        name: 'Okabe-Ito (Colorblind Safe, Recommended)',
        type: 'preset',
        is_default: true,
        colors: {
            primary: '#0072B2',
            secondary: '#E69F00',
            tertiary: '#009E73',
            text: '#333333',
            fill: '#FFFFFF',
            section_bg: '#F7F7F7',
            border: '#CCCCCC',
            arrow: '#4D4D4D',
        },
    },
    {
        id: 'preset-ml-topconf-tab10',
        name: 'ML TopConf (Matplotlib Tab10)',
        type: 'preset',
        colors: {
            primary: '#1F77B4',
            secondary: '#FF7F0E',
            tertiary: '#2CA02C',
            text: '#1F2937',
            fill: '#FFFFFF',
            section_bg: '#F8FAFC',
            border: '#CBD5E1',
            arrow: '#334155',
        },
    },
    {
        id: 'preset-ml-topconf-colorblind',
        name: 'ML TopConf (Seaborn Colorblind)',
        type: 'preset',
        colors: {
            primary: '#0173B2',
            secondary: '#DE8F05',
            tertiary: '#029E73',
            text: '#1F2937',
            fill: '#FFFFFF',
            section_bg: '#F8FAFC',
            border: '#CBD5E1',
            arrow: '#334155',
        },
    },
    {
        id: 'preset-ml-topconf-deep',
        name: 'ML TopConf (Seaborn Deep)',
        type: 'preset',
        colors: {
            primary: '#4C72B0',
            secondary: '#DD8452',
            tertiary: '#55A868',
            text: '#1F2937',
            fill: '#FFFFFF',
            section_bg: '#F8FAFC',
            border: '#CBD5E1',
            arrow: '#334155',
        },
    },
];

export function ColorSchemes() {
    const [schemes, setSchemes] = useState<ColorScheme[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    // Custom form state
    const [name, setName] = useState('');
    const [colors, setColors] = useState({
        primary: '#0072B2',
        secondary: '#E69F00',
        tertiary: '#009E73',
        text: '#333333',
        fill: '#FFFFFF',
        section_bg: '#F7F7F7',
        border: '#CCCCCC',
        arrow: '#4D4D4D'
    });

    useEffect(() => {
        fetchSchemes();
    }, []);

    const fetchSchemes = async () => {
        setIsLoading(true);
        try {
            const res = await api.get('/color-schemes/');
            setSchemes(res.data || []);
        } catch (e) {
            console.error(e);
            setSchemes(FALLBACK_PRESETS);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async () => {
        try {
            await api.post('/color-schemes/', { name, colors });
            fetchSchemes();
            setIsDialogOpen(false);
            setName('');
        } catch (e) {
            console.error(e);
            alert('Failed to save color scheme');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this color scheme?')) return;
        try {
            await api.delete(`/color-schemes/${id}`);
            fetchSchemes();
        } catch (e) {
            console.error(e);
        }
    };

    if (isLoading) return <div className="p-8 text-center text-muted-foreground">加载中...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">自定义配色方案</h1>
                    <p className="text-muted-foreground mt-1">管理您的个性化论文配图颜色组合。</p>
                </div>

                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogTrigger asChild>
                        <Button><Plus className="mr-2 h-4 w-4" /> 新建配色</Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>创建配色方案</DialogTitle>
                            <DialogDescription>为学术图表添加新的自定义调色板。</DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="name" className="text-right">名称</Label>
                                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} className="col-span-3" />
                            </div>
                            {Object.entries(colors).map(([key, value]) => (
                                <div key={key} className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor={key} className="text-right capitalize">{key.replace('_', ' ')}</Label>
                                    <div className="col-span-3 flex gap-2">
                                        <Input id={key} type="color" value={value} onChange={(e) => setColors({ ...colors, [key]: e.target.value })} className="w-16 p-1 h-10" />
                                        <Input value={value} onChange={(e) => setColors({ ...colors, [key]: e.target.value })} className="flex-1 font-mono uppercase" />
                                    </div>
                                </div>
                            ))}
                        </div>
                        <DialogFooter>
                            <Button onClick={handleCreate}>Save Palette</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {schemes.map((scheme) => {
                    const isPreset = scheme.type === 'preset';
                    return (
                        <Card key={scheme.id}>
                        <CardHeader className="pb-3 border-b">
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-lg">{scheme.name}</CardTitle>
                                {!isPreset && (
                                    <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive -mt-1 -mr-2" onClick={() => handleDelete(scheme.id)}>
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                )}
                                {isPreset && <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground">Preset</span>}
                            </div>
                        </CardHeader>
                        <CardContent className="pt-4">
                            <div className="grid grid-cols-4 gap-2">
                                {Object.entries(scheme.colors).map(([key, color]) => (
                                    <div key={key} className="flex flex-col items-center">
                                        <div className="w-10 h-10 rounded-full border shadow-sm mb-2" style={{ backgroundColor: color }} title={color} />
                                        <span className="text-[10px] text-muted-foreground truncate w-full text-center capitalize">{key.replace('_', '')}</span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
