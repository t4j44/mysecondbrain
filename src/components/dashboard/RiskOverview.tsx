'use client';

import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  Legend,
  PolarAngleAxis,
} from 'recharts';

// Types
interface RiskMetric {
  id: string;
  name: string;
  category: string;
  score: number;
  status: 'low' | 'medium' | 'high' | 'critical';
  trend: 'up' | 'down' | 'stable';
  change: string;
}

interface ThreatLog {
  id: string;
  timestamp: string;
  event: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  source: string;
}

// Dummy Data
const velocityDataMap = {
  '24h': [
    { time: '00:00', velocity: 22, baseline: 30, spike: 0 },
    { time: '04:00', velocity: 18, baseline: 30, spike: 0 },
    { time: '08:00', velocity: 45, baseline: 32, spike: 50 },
    { time: '12:00', velocity: 74, baseline: 35, spike: 78 },
    { time: '16:00', velocity: 38, baseline: 32, spike: 0 },
    { time: '20:00', velocity: 58, baseline: 30, spike: 62 },
    { time: '24:00', velocity: 29, baseline: 30, spike: 0 },
  ],
  '7d': [
    { time: 'Mon', velocity: 32, baseline: 30, spike: 0 },
    { time: 'Tue', velocity: 48, baseline: 30, spike: 55 },
    { time: 'Wed', velocity: 65, baseline: 32, spike: 70 },
    { time: 'Thu', velocity: 42, baseline: 32, spike: 0 },
    { time: 'Fri', velocity: 81, baseline: 35, spike: 85 },
    { time: 'Sat', velocity: 25, baseline: 28, spike: 0 },
    { time: 'Sun', velocity: 19, baseline: 28, spike: 0 },
  ],
  '30d': [
    { time: 'Week 1', velocity: 35, baseline: 30, spike: 40 },
    { time: 'Week 2', velocity: 52, baseline: 30, spike: 60 },
    { time: 'Week 3', velocity: 44, baseline: 32, spike: 0 },
    { time: 'Week 4', velocity: 68, baseline: 32, spike: 75 },
  ],
};

const complianceScores = [
  { name: 'GDPR', score: 98, fill: '#10b981' },
  { name: 'HIPAA', score: 92, fill: '#06b6d4' },
  { name: 'ISO 27001', score: 88, fill: '#6366f1' },
  { name: 'SOC 2', score: 95, fill: '#8b5cf6' },
];

const riskMetrics: RiskMetric[] = [
  {
    id: 'm-1',
    name: 'API Rate Anomaly',
    category: 'Infrastructure',
    score: 18,
    status: 'low',
    trend: 'down',
    change: '-12%',
  },
  {
    id: 'm-2',
    name: 'Auth Surge',
    category: 'Security',
    score: 64,
    status: 'high',
    trend: 'up',
    change: '+34%',
  },
  {
    id: 'm-3',
    name: 'Data Exfiltration Risk',
    category: 'Data Privacy',
    score: 32,
    status: 'medium',
    trend: 'stable',
    change: '0%',
  },
  {
    id: 'm-4',
    name: 'IAM Privilege Creep',
    category: 'Access Control',
    score: 12,
    status: 'low',
    trend: 'down',
    change: '-5%',
  },
];

const liveThreatLogs: ThreatLog[] = [
  {
    id: 't-1',
    timestamp: '2 mins ago',
    event: 'Unusual IP login attempt (EU-West)',
    severity: 'medium',
    source: 'AuthGateway',
  },
  {
    id: 't-2',
    timestamp: '14 mins ago',
    event: 'Token refresh rate spike detected',
    severity: 'high',
    source: 'OAuth2 Server',
  },
  {
    id: 't-3',
    timestamp: '1 hour ago',
    event: 'Automated compliance scan passed',
    severity: 'low',
    source: 'SOC2 Monitor',
  },
];

// Helper Badge Component for Status Colors
const StatusBadge: React.FC<{ status: 'low' | 'medium' | 'high' | 'critical' }> = ({ status }) => {
  const styles = {
    low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    high: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    critical: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  };

  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium rounded-full border ${styles[status]} capitalize inline-flex items-center gap-1`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          status === 'low'
            ? 'bg-emerald-400'
            : status === 'medium'
            ? 'bg-amber-400'
            : status === 'high'
            ? 'bg-rose-400'
            : 'bg-purple-400'
        }`}
      />
      {status}
    </span>
  );
};

// Custom Glassmorphic Tooltip for AreaChart
const VelocityTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/90 border border-white/10 backdrop-blur-md p-3 rounded-lg shadow-xl text-xs space-y-1">
        <p className="font-semibold text-slate-200">{label}</p>
        <p className="text-purple-400">
          Risk Velocity: <span className="font-bold text-white">{payload[0]?.value} pts</span>
        </p>
        {payload[1] && (
          <p className="text-slate-400">
            Baseline: <span className="font-medium text-slate-300">{payload[1]?.value} pts</span>
          </p>
        )}
      </div>
    );
  }
  return null;
};

// Custom Tooltip for RadialBar
const ComplianceTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900/90 border border-white/10 backdrop-blur-md p-2.5 rounded-lg shadow-xl text-xs">
        <p className="font-semibold text-white">{data.name}</p>
        <p className="text-emerald-400 font-bold">{data.score}% Compliant</p>
      </div>
    );
  }
  return null;
};

export default function RiskOverview() {
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');
  const [activeTab, setActiveTab] = useState<'all' | 'critical'>('all');

  const currentVelocityData = velocityDataMap[timeRange];

  return (
    <section className="w-full max-w-7xl mx-auto p-4 sm:p-6 space-y-6 text-slate-100 font-sans">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white/5 border border-white/10 backdrop-blur-md p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-xs uppercase tracking-wider text-emerald-400 font-mono font-semibold">
              Live Monitoring
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Real-time Risk Dashboard</h2>
          <p className="text-sm text-slate-400">
            Continuous threat velocity telemetry, regulatory compliance posture, and risk alerts.
          </p>
        </div>

        {/* Action Controls / Time range picker */}
        <div className="flex items-center gap-2 bg-slate-950/40 p-1.5 rounded-xl border border-white/10 self-start sm:self-center">
          {(['24h', '7d', '30d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                timeRange === range
                  ? 'bg-purple-600/80 text-white shadow-lg shadow-purple-500/20 border border-purple-400/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {range.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Main Responsive Grid Layout: grid-cols-1 → grid-cols-3 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card 1: Risk Velocity (AreaChart) - Spans 1 col (or 2 cols on lg) */}
        <div className="lg:col-span-2 bg-white/5 border border-white/10 backdrop-blur-md p-5 rounded-2xl flex flex-col justify-between space-y-4 hover:border-white/20 transition-all">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                  />
                </svg>
                Risk Velocity
              </h3>
              <p className="text-xs text-slate-400">Rate of risk score accumulation over time</p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-purple-400 font-mono">42.5</span>
              <span className="text-xs text-slate-400 block">Avg Index</span>
            </div>
          </div>

          {/* AreaChart Container */}
          <div className="w-full h-64 sm:h-72 pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={currentVelocityData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="riskVelocityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="baselineGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#64748b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#64748b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                <XAxis
                  dataKey="time"
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
                  domain={[0, 100]}
                />
                <Tooltip content={<VelocityTooltip />} />
                <Area
                  type="monotone"
                  dataKey="velocity"
                  stroke="#a855f7"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#riskVelocityGrad)"
                  name="Risk Velocity"
                />
                <Area
                  type="monotone"
                  dataKey="baseline"
                  stroke="#64748b"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  fillOpacity={1}
                  fill="url(#baselineGrad)"
                  name="Baseline"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/5">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block" />
                Live Velocity
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-500 inline-block" />
                Expected Baseline
              </span>
            </div>
            <span className="font-mono text-emerald-400">Normal Range (&lt; 75)</span>
          </div>
        </div>

        {/* Card 2: Compliance Score (RadialBar) */}
        <div className="bg-white/5 border border-white/10 backdrop-blur-md p-5 rounded-2xl flex flex-col justify-between space-y-4 hover:border-white/20 transition-all">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-emerald-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
                Compliance Score
              </h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                93.2% Total
              </span>
            </div>
            <p className="text-xs text-slate-400">Framework audit alignment & posture</p>
          </div>

          {/* RadialBarChart Container */}
          <div className="w-full h-64 sm:h-72 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart
                cx="50%"
                cy="50%"
                innerRadius="25%"
                outerRadius="90%"
                barSize={12}
                data={complianceScores}
                startAngle={180}
                endAngle={-180}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                <RadialBar
                  background={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                  dataKey="score"
                  cornerRadius={8}
                />
                <Tooltip content={<ComplianceTooltip />} />
                <Legend
                  iconSize={8}
                  layout="vertical"
                  verticalAlign="bottom"
                  align="center"
                  wrapperStyle={{
                    fontSize: '11px',
                    color: '#94a3b8',
                    paddingTop: '10px',
                  }}
                />
              </RadialBarChart>
            </ResponsiveContainer>

            {/* Inner Radial Center Text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none pb-8">
              <span className="text-2xl font-bold text-white font-mono">93.2%</span>
              <span className="text-[10px] text-slate-400 uppercase tracking-widest">
                Compliance
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs">
            <span className="text-slate-400">Last Audit: 2 hours ago</span>
            <span className="text-purple-400 hover:underline cursor-pointer">
              Download Report &rarr;
            </span>
          </div>
        </div>

        {/* Card 3: Real-time Indicators & Threat Stream */}
        <div className="md:col-span-2 lg:col-span-3 bg-white/5 border border-white/10 backdrop-blur-md p-5 rounded-2xl space-y-5 hover:border-white/20 transition-all">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/10">
            <div>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-amber-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                Key Risk Indicators & Active Telemetry
              </h3>
              <p className="text-xs text-slate-400">
                Automated risk vectors and continuous security signal assessment
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-3 py-1 text-xs rounded-lg transition-all ${
                  activeTab === 'all'
                    ? 'bg-white/10 text-white font-medium border border-white/10'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                All Metrics
              </button>
              <button
                onClick={() => setActiveTab('critical')}
                className={`px-3 py-1 text-xs rounded-lg transition-all ${
                  activeTab === 'critical'
                    ? 'bg-white/10 text-white font-medium border border-white/10'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                High Risk Only
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {riskMetrics
              .filter((m) => activeTab === 'all' || m.status === 'high' || m.status === 'critical')
              .map((metric) => (
                <div
                  key={metric.id}
                  className="bg-slate-900/40 border border-white/5 p-3.5 rounded-xl space-y-2 hover:bg-slate-900/60 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-medium">{metric.category}</span>
                    <StatusBadge status={metric.status} />
                  </div>
                  <h4 className="text-sm font-semibold text-white truncate">{metric.name}</h4>
                  <div className="flex items-baseline justify-between pt-1">
                    <span className="text-xl font-bold font-mono text-white">{metric.score}</span>
                    <span
                      className={`text-xs font-mono font-medium ${
                        metric.trend === 'up'
                          ? 'text-rose-400'
                          : metric.trend === 'down'
                          ? 'text-emerald-400'
                          : 'text-slate-400'
                      }`}
                    >
                      {metric.change}
                    </span>
                  </div>
                </div>
              ))}
          </div>

          {/* Live Threat Log Stream */}
          <div className="pt-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 font-mono">
              Recent Threat Signals
            </h4>
            <div className="space-y-2">
              {liveThreatLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/30 border border-white/5 text-xs text-slate-300 hover:border-white/10 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <StatusBadge status={log.severity} />
                    <span className="font-medium text-slate-200">{log.event}</span>
                  </div>
                  <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
                    <span>Source: {log.source}</span>
                    <span>{log.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
