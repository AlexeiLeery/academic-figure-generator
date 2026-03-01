import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';

export function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const setAuth = useAuthStore((state) => state.setAuth);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            const response = await api.post('/auth/login', { email, password });
            const { access_token, refresh_token } = response.data;

            // Fetch user profile
            const userResponse = await api.get('/auth/me', {
                headers: { Authorization: `Bearer ${access_token}` }
            });

            setAuth(access_token, refresh_token, userResponse.data);
            navigate('/projects');
        } catch (err: any) {
            setError(err.response?.data?.detail || '登录失败，请检查您的邮箱和密码。');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex">
            {/* Left decorative panel */}
            <div
                className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden"
                style={{
                    background: 'linear-gradient(135deg, #0a0f1e 0%, #0d1b3e 30%, #0f2460 55%, #1a2f72 75%, #0e1a4a 100%)',
                }}
            >
                {/* Dot grid pattern overlay */}
                <div
                    className="absolute inset-0 opacity-20"
                    style={{
                        backgroundImage: 'radial-gradient(circle, #6b9fff 1px, transparent 1px)',
                        backgroundSize: '32px 32px',
                    }}
                />

                {/* Soft glow blobs */}
                <div
                    className="absolute top-1/4 left-1/3 w-72 h-72 rounded-full opacity-20 blur-3xl pointer-events-none"
                    style={{ background: 'radial-gradient(circle, #3b82f6, transparent)' }}
                />
                <div
                    className="absolute bottom-1/4 right-1/4 w-56 h-56 rounded-full opacity-15 blur-3xl pointer-events-none"
                    style={{ background: 'radial-gradient(circle, #818cf8, transparent)' }}
                />

                {/* Top: Logo + App name */}
                <div className="relative z-10 flex items-center gap-3">
                    <img
                        src="/logo.jpg"
                        alt="Logo"
                        className="w-10 h-10 rounded-xl object-cover"
                        style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.12)' }}
                    />
                    <span className="text-white font-semibold text-base tracking-tight">
                        科研配图生成器
                    </span>
                </div>

                {/* Center: tagline */}
                <div className="relative z-10 space-y-5">
                    <h2
                        className="text-4xl font-bold leading-tight text-white"
                        style={{ letterSpacing: '-0.02em' }}
                    >
                        让学术图表<br />
                        <span style={{ color: '#93c5fd' }}>精准传达</span><br />
                        您的研究成果
                    </h2>
                    <p className="text-base leading-relaxed" style={{ color: 'rgba(255,255,255,0.5)' }}>
                        智能生成符合顶级期刊规范的<br />
                        专业学术配图，一键导出，即刻投稿。
                    </p>
                </div>

                {/* Bottom: subtle footer */}
                <div className="relative z-10">
                    <p className="text-xs" style={{ color: 'rgba(255,255,255,0.25)' }}>
                        © 2025 科研配图生成器. All rights reserved.
                    </p>
                </div>
            </div>

            {/* Right form panel */}
            <div className="flex-1 flex items-center justify-center bg-white px-6 py-12">
                <div className="w-full max-w-sm">
                    {/* Mobile-only logo */}
                    <div className="flex justify-center mb-8 lg:hidden">
                        <img src="/logo.jpg" alt="Logo" className="w-12 h-12 rounded-xl object-cover" />
                    </div>

                    {/* Heading */}
                    <div className="mb-8">
                        <h1
                            className="text-3xl font-bold text-gray-900 mb-2"
                            style={{ letterSpacing: '-0.025em' }}
                        >
                            欢迎回来
                        </h1>
                        <p className="text-sm text-gray-500">
                            请输入您的账号信息以继续
                        </p>
                    </div>

                    {/* Error alert */}
                    {error && (
                        <div className="mb-6">
                            <Alert variant="destructive" className="border-red-200 bg-red-50 text-red-700 rounded-xl">
                                <AlertDescription className="text-sm">{error}</AlertDescription>
                            </Alert>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleLogin} className="space-y-5">
                        <div className="space-y-1.5">
                            <Label
                                htmlFor="email"
                                className="text-sm font-medium text-gray-700"
                            >
                                邮箱地址
                            </Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="h-11 px-4 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-gray-400 focus:ring-0 transition-colors duration-200"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <Label
                                htmlFor="password"
                                className="text-sm font-medium text-gray-700"
                            >
                                密码
                            </Label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="h-11 px-4 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-gray-400 focus:ring-0 transition-colors duration-200"
                            />
                        </div>

                        <Button
                            type="submit"
                            disabled={isLoading}
                            className="w-full h-11 rounded-xl text-sm font-semibold tracking-wide transition-all duration-200"
                            style={{
                                background: isLoading ? '#374151' : '#111827',
                                color: '#ffffff',
                                border: 'none',
                            }}
                        >
                            {isLoading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg
                                        className="animate-spin h-4 w-4 text-white"
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                    </svg>
                                    登录中...
                                </span>
                            ) : (
                                '登 录'
                            )}
                        </Button>
                    </form>

                    {/* Divider */}
                    <div className="my-6 flex items-center gap-3">
                        <div className="flex-1 h-px bg-gray-100" />
                        <span className="text-xs text-gray-400">或</span>
                        <div className="flex-1 h-px bg-gray-100" />
                    </div>

                    {/* Register link */}
                    <p className="text-center text-sm text-gray-500">
                        还没有账号？{' '}
                        <Link
                            to="/register"
                            className="font-semibold text-gray-900 hover:text-gray-600 transition-colors duration-150 underline underline-offset-2 decoration-gray-300 hover:decoration-gray-500"
                        >
                            立即注册
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
