import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Activity, Coins, Image as ImageIcon, MessageSquare } from 'lucide-react';

export function Usage() {
    const [summary, setSummary] = useState<any>(null);
    const [breakdown, setBreakdown] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchUsageData();
    }, []);

    const fetchUsageData = async () => {
        setIsLoading(true);
        try {
            const summaryRes = await api.get('/usage/summary');
            setSummary(summaryRes.data);

            const breakdownRes = await api.get('/usage/breakdown');
            setBreakdown(breakdownRes.data);
        } catch (e) {
            console.error(e);
            // Fallback mock data
            setSummary({
                billing_period: '2026-03',
                claude_tokens_used: 125430,
                claude_calls: 42,
                nanobanana_images: 15,
                estimated_cost_usd: 3.45,
                quota_claude_remaining: 874570,
                quota_images_remaining: 85
            });
            setBreakdown([
                { api_name: 'Claude 3.5 Sonnet', total_calls: 42, success_count: 40, failure_count: 2, total_tokens: 125430, total_cost_usd: 1.25, avg_duration_ms: 4500 },
                { api_name: 'NanoBanana V2', total_calls: 15, success_count: 15, failure_count: 0, total_tokens: 0, total_cost_usd: 2.20, avg_duration_ms: 12000 }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading && !summary) return <div className="p-8">加载用量数据中...</div>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">用量看板</h1>
                <p className="text-muted-foreground mt-1">查看 {summary?.billing_period} 账单周期的 Token 消耗及预估费用</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">预估总费用</CardTitle>
                        <Coins className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">¥{summary?.estimated_cost_usd ? (summary.estimated_cost_usd * 7.2).toFixed(2) : '0.00'}</div>
                        <p className="text-xs text-muted-foreground mt-1">当前账单周期</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Claude Token消耗</CardTitle>
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{(summary?.claude_tokens_used || 0).toLocaleString()}</div>
                        <p className="text-xs text-muted-foreground mt-1">剩余额度：{summary?.quota_claude_remaining?.toLocaleString()}</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">已生成配图</CardTitle>
                        <ImageIcon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary?.nanobanana_images || 0}</div>
                        <p className="text-xs text-muted-foreground mt-1">剩余额度：{summary?.quota_images_remaining}</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">API 调用次数</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary?.claude_calls || 0}</div>
                        <p className="text-xs text-muted-foreground mt-1">总请求成功次数</p>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="breakdown" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="breakdown">API 消耗明细</TabsTrigger>
                    <TabsTrigger value="history">历史趋势</TabsTrigger>
                </TabsList>
                <TabsContent value="breakdown" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>模型调用分布</CardTitle>
                            <CardDescription>详细查看各项 API 的调用次数、成功率与费用。</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>模型 / API</TableHead>
                                        <TableHead className="text-right">调用次数</TableHead>
                                        <TableHead className="text-right">成功率</TableHead>
                                        <TableHead className="text-right">Token 消耗</TableHead>
                                        <TableHead className="text-right">平均延迟</TableHead>
                                        <TableHead className="text-right">预估花费</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {breakdown.map((item, idx) => (
                                        <TableRow key={idx}>
                                            <TableCell className="font-medium">{item.api_name}</TableCell>
                                            <TableCell className="text-right">{item.total_calls}</TableCell>
                                            <TableCell className="text-right">
                                                {item.total_calls > 0 ? Math.round((item.success_count / item.total_calls) * 100) : 0}%
                                            </TableCell>
                                            <TableCell className="text-right">{item.total_tokens > 0 ? item.total_tokens.toLocaleString() : '-'}</TableCell>
                                            <TableCell className="text-right">{(item.avg_duration_ms / 1000).toFixed(1)}s</TableCell>
                                            <TableCell className="text-right">¥{(item.total_cost_usd * 7.2).toFixed(2)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="history" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>历史用量趋势</CardTitle>
                            <CardDescription>查看过去 30 天的 API 调用和费用趋势。(演示图表表位)</CardDescription>
                        </CardHeader>
                        <CardContent className="h-80 flex items-center justify-center border-t bg-muted/10">
                            <p className="text-muted-foreground">图表可视化将在此区域渲染 (例如使用 Recharts)</p>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
