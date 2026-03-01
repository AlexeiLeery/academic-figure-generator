import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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

                {/* Center: feature list */}
                <div className="relative z-10 space-y-8">
                    <div className="space-y-4">
                        <h2
                            className="text-4xl font-bold leading-tight text-white"
                            style={{ letterSpacing: '-0.02em' }}
                        >
                            开启您的<br />
                            <span style={{ color: '#93c5fd' }}>科研配图</span><br />
                            新体验
                        </h2>
                        <p className="text-base leading-relaxed" style={{ color: 'rgba(255,255,255,0.5)' }}>
                            注册即可免费体验 AI 驱动的<br />
                            学术图表生成与排版功能。
                        </p>
                    </div>

                    {/* Feature pills */}
                    <div className="space-y-3">
                        {[
                            '符合 Nature / Science 投稿规范',
                            '支持多种图表类型一键生成',
                            '高分辨率矢量导出，即刻可用',
                        ].map((feat) => (
                            <div key={feat} className="flex items-center gap-3">
                                <div
                                    className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                                    style={{ background: 'rgba(147,197,253,0.15)', border: '1px solid rgba(147,197,253,0.3)' }}
                                >
                                    <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
                                        <path d="M2 6l3 3 5-5" stroke="#93c5fd" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </div>
                                <span className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>
                                    {feat}
                                </span>
                            </div>
                        ))}
                    </div>
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
                            创建账号
                        </h1>
                        <p className="text-sm text-gray-500">
                            填写以下信息，免费开始使用
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
                    <form onSubmit={handleRegister} className="space-y-5">
                        <div className="space-y-1.5">
                            <Label
                                htmlFor="displayName"
                                className="text-sm font-medium text-gray-700"
                            >
                                显示名称
                            </Label>
                            <Input
                                id="displayName"
                                placeholder="例如：张三"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                required
                                className="h-11 px-4 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-gray-400 focus:ring-0 transition-colors duration-200"
                            />
                        </div>

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
                                    创建中...
                                </span>
                            ) : (
                                '注 册'
                            )}
                        </Button>

                        <p className="text-xs text-gray-400 text-center leading-relaxed">
                            注册即表示您同意我们的
                            <span className="text-gray-600 underline underline-offset-2 decoration-gray-300 cursor-pointer"> 服务条款 </span>
                            与
                            <span className="text-gray-600 underline underline-offset-2 decoration-gray-300 cursor-pointer"> 隐私政策</span>
                        </p>
                    </form>

                    {/* Divider */}
                    <div className="my-6 flex items-center gap-3">
                        <div className="flex-1 h-px bg-gray-100" />
                        <span className="text-xs text-gray-400">或</span>
                        <div className="flex-1 h-px bg-gray-100" />
                    </div>

                    {/* Login link */}
                    <p className="text-center text-sm text-gray-500">
                        已有账号？{' '}
                        <Link
                            to="/login"
                            className="font-semibold text-gray-900 hover:text-gray-600 transition-colors duration-150 underline underline-offset-2 decoration-gray-300 hover:decoration-gray-500"
                        >
                            立即登录
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
