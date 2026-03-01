import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';

export function Register() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await api.post('/auth/register', {
                email,
                password,
                display_name: displayName
            });

            // Auto redirect to login
            navigate('/login', { state: { message: '注册成功，请登录。' } });
        } catch (err: any) {
            setError(err.response?.data?.detail || '注册失败，请重试。');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/30">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1 text-center">
                    <CardTitle className="text-2xl font-bold text-primary">创建账号</CardTitle>
                    <CardDescription>请输入您的信息以注册账号</CardDescription>
                </CardHeader>
                <form onSubmit={handleRegister}>
                    <CardContent className="space-y-4">
                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="displayName">显示名称</Label>
                            <Input
                                id="displayName"
                                placeholder="例如：张三"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="email">邮箱</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="m@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">密码</Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col space-y-4">
                        <Button className="w-full" type="submit" disabled={isLoading}>
                            {isLoading ? '创建中...' : '注 册'}
                        </Button>
                        <div className="text-sm text-center text-muted-foreground">
                            已有账号？{' '}
                            <Link to="/login" className="text-primary hover:underline">
                                立即登录
                            </Link>
                        </div>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}
