import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

export function Settings() {
    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">应用设置</h1>
                <p className="text-muted-foreground mt-1">管理 API 密钥和应用配置。</p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>API 配置</CardTitle>
                    <CardDescription>
                        当前 API 密钥通过项目根目录的 <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">.env</code> 文件管理。
                        修改后请重启后端服务。
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Claude Section */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-foreground">Claude Agent SDK (Anthropic)</h4>
                        <div className="space-y-2">
                            <Label>ANTHROPIC_API_KEY</Label>
                            <Input
                                type="password"
                                placeholder="在 .env 文件中配置"
                                disabled
                                value="••••••••"
                            />
                            <p className="text-xs text-muted-foreground">
                                用于 Prompt 生成。配置方式：编辑 <code className="font-mono">.env</code> 文件中的 <code className="font-mono">ANTHROPIC_API_KEY</code> 字段。
                            </p>
                        </div>
                    </div>

                    <hr className="border-muted" />

                    {/* NanoBanana Section */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-foreground">NanoBanana 配图服务</h4>
                        <div className="space-y-2">
                            <Label>NANOBANANA_API_KEY</Label>
                            <Input
                                type="password"
                                placeholder="在 .env 文件中配置"
                                disabled
                                value="••••••••"
                            />
                            <p className="text-xs text-muted-foreground">
                                用于图片生成。配置方式：编辑 <code className="font-mono">.env</code> 文件中的 <code className="font-mono">NANOBANANA_API_KEY</code> 字段。
                            </p>
                        </div>
                        <div className="space-y-2">
                            <Label>NANOBANANA_API_BASE</Label>
                            <Input
                                type="text"
                                placeholder="https://api.keepgo.icu"
                                disabled
                                value="https://api.keepgo.icu"
                            />
                            <p className="text-xs text-muted-foreground">
                                NanoBanana API 地址。默认值：<code className="font-mono">https://api.keepgo.icu</code>
                            </p>
                        </div>
                    </div>
                </CardContent>
                <CardFooter className="border-t bg-muted/40 p-4">
                    <div className="text-xs text-muted-foreground">
                        💡 提示：修改 .env 文件后，请运行 <code className="font-mono bg-muted px-1.5 py-0.5 rounded">uvicorn app.main:app --reload</code> 重启后端。
                    </div>
                </CardFooter>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>数据存储</CardTitle>
                    <CardDescription>应用数据存储在本地文件系统中。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <Label className="text-muted-foreground">数据库</Label>
                            <p className="mt-1 font-mono text-xs">backend/data/app.db</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">上传文件</Label>
                            <p className="mt-1 font-mono text-xs">backend/data/uploads/</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">生成图片</Label>
                            <p className="mt-1 font-mono text-xs">backend/data/figures/</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
