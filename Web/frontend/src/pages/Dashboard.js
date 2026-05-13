import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  RefreshCw,
  Download,
  Search,
  Network,
  TrendingUp,
  BarChart3,
  AlertTriangle,
  Activity,
  Circle,
  Info,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import Button from '../components/ui/button';
import Card from '../components/ui/card';
import Navbar from '../components/Navbar';
import { useNavigate } from 'react-router-dom';

const STORAGE_KEY = 'bothunter_hashtag_scans';
const CHART_COLORS = ['#ff4757', '#00ff88', '#00d9ff', '#ffa502', '#7c4dff', '#36cfc9'];

const formatTimeAgo = (isoTime) => {
  if (!isoTime) return 'Unknown';
  const ts = new Date(isoTime).getTime();
  if (Number.isNaN(ts)) return 'Unknown';

  const diffMs = Date.now() - ts;
  const diffMin = Math.max(0, Math.floor(diffMs / 60000));
  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;

  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
};

const tooltipStyle = {
  backgroundColor: '#0f1530',
  border: '1px solid rgba(0, 217, 255, 0.3)',
  borderRadius: '8px',
};

const tooltipTextStyle = {
  color: '#e2e8f0',
};

const infoTagStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '9999px',
  border: '1px solid rgba(34, 211, 238, 0.3)',
  backgroundColor: 'rgba(34, 211, 238, 0.1)',
  padding: '0.375rem',
  color: 'rgb(165, 243, 252)',
  lineHeight: 1,
};

const CardInfoTag = ({ label }) => (
  <div className="group relative inline-flex items-center" style={infoTagStyle}>
    <Info className="h-3.5 w-3.5" style={{ color: 'rgb(165, 243, 252)' }} />
    <span className="pointer-events-none absolute right-0 top-full z-20 mt-2 w-56 rounded-lg border border-border bg-background/95 px-3 py-2 text-left text-xs leading-relaxed text-muted-foreground opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
      {label}
    </span>
  </div>
);

const Dashboard = () => {
  const navigate = useNavigate();
  const dashboardReportRef = useRef(null);
  const headerScrollRef = useRef(0);
  const [scans, setScans] = useState([]);
  const [selectedHashtag, setSelectedHashtag] = useState('all');
  const [scanWindow, setScanWindow] = useState('all');
  const [minBotRatio, setMinBotRatio] = useState(0);
  const [headerVisible, setHeaderVisible] = useState(true);

  const loadDashboardData = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      setScans(Array.isArray(saved) ? saved : []);
    } catch (error) {
      setScans([]);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY < 12) {
        setHeaderVisible(true);
      } else if (currentScrollY > headerScrollRef.current + 8) {
        setHeaderVisible(false);
      } else if (currentScrollY < headerScrollRef.current - 8) {
        setHeaderVisible(true);
      }

      headerScrollRef.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const latestScan = scans[0] || null;

  const availableHashtags = useMemo(() => {
    return [...new Set(scans.map((scan) => scan.hashtag).filter(Boolean))].sort((a, b) => a.localeCompare(b));
  }, [scans]);

  const filteredScans = useMemo(() => {
    let nextScans = [...scans];

    if (selectedHashtag !== 'all') {
      nextScans = nextScans.filter((scan) => scan.hashtag === selectedHashtag);
    }

    if (scanWindow !== 'all') {
      const limit = Number(scanWindow);
      nextScans = nextScans.slice(0, limit);
    }

    if (minBotRatio > 0) {
      nextScans = nextScans.filter((scan) => (scan.bot_ratio || 0) * 100 >= minBotRatio);
    }

    return nextScans;
  }, [scans, selectedHashtag, scanWindow, minBotRatio]);

  const activeHashtagLabel = selectedHashtag === 'all' ? 'All hashtags' : `#${selectedHashtag}`;
  const activeWindowLabel = scanWindow === 'all' ? 'All scans' : `Latest ${scanWindow} scans`;
  const noResultsForFilters = scans.length > 0 && filteredScans.length === 0;
  const latestSuspiciousCount = latestScan?.top_suspicious_accounts?.length || 0;

  const EmptyState = ({ title, description }) => (
    <div className="flex flex-col items-center justify-center py-12 text-center min-h-[240px]">
      <div className="w-16 h-16 rounded-full bg-primary/10 border-2 border-primary/30 flex items-center justify-center mb-4">
        <AlertTriangle className="h-8 w-8 text-primary/50" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-4 max-w-md">{description}</p>
      <Button variant="hero" size="sm" onClick={() => navigate('/new-scan')}>
        Start New Scan
      </Button>
    </div>
  );

  const recentDetections = useMemo(() => {
    const sourceScan = filteredScans[0] || latestScan;
    if (!sourceScan?.top_suspicious_accounts?.length) return [];
    return sourceScan.top_suspicious_accounts.map((account) => {
      const isBot = account.label === 'bot';
      return {
        username: `@${account.username}`,
        type: `#${sourceScan.hashtag}`,
        risk: isBot
          ? `BOT ${(account.bot_probability * 100).toFixed(1)}%`
          : `HUMAN ${(account.human_probability * 100).toFixed(1)}%`,
        riskColor: isBot ? 'text-destructive' : 'text-success',
        dotColor: isBot ? 'text-destructive' : 'text-success',
        time: formatTimeAgo(sourceScan.scanned_at),
      };
    });
  }, [filteredScans, latestScan]);

  const activityTimeline = useMemo(() => {
    return filteredScans.slice(0, 8).map((scan) => ({
      time: formatTimeAgo(scan.scanned_at),
      event: `Scanned #${scan.hashtag}: ${scan.bots_detected} bots in ${scan.analyzed_accounts} accounts`,
      color: scan.bots_detected > 0 ? 'text-destructive' : 'text-success',
    }));
  }, [filteredScans]);

  const trendData = useMemo(() => {
    return [...filteredScans]
      .reverse()
      .slice(-20)
      .map((scan, index) => ({
        name: `S${index + 1}`,
        hashtag: `#${scan.hashtag}`,
        botRatio: Number(((scan.bot_ratio || 0) * 100).toFixed(1)),
      }));
  }, [filteredScans]);

  const rankingData = useMemo(() => {
    const grouped = filteredScans.reduce((acc, scan) => {
      const key = `#${scan.hashtag}`;
      if (!acc[key]) {
        acc[key] = {
          hashtag: key,
          totalRatio: 0,
          count: 0,
        };
      }
      acc[key].totalRatio += scan.bot_ratio || 0;
      acc[key].count += 1;
      return acc;
    }, {});

    return Object.values(grouped)
      .map((item) => ({
        hashtag: item.hashtag,
        avgBotRatio: Number(((item.totalRatio / item.count) * 100).toFixed(1)),
      }))
      .sort((a, b) => b.avgBotRatio - a.avgBotRatio)
      .slice(0, 8);
  }, [filteredScans]);

  const compositionData = useMemo(() => {
    const bots = filteredScans.reduce((sum, scan) => sum + (scan.bots_detected || 0), 0);
    const humans = filteredScans.reduce((sum, scan) => sum + (scan.humans_detected || 0), 0);
    return [
      { name: 'Bots', value: bots },
      { name: 'Humans', value: humans },
    ];
  }, [filteredScans]);

  const stats = useMemo(() => {
    const totalBots = filteredScans.reduce((sum, scan) => sum + (scan.bots_detected || 0), 0);
    const totalTweets = filteredScans.reduce((sum, scan) => sum + (scan.total_tweets || 0), 0);
    const uniqueHashtags = new Set(filteredScans.map((scan) => scan.hashtag)).size;
    const avgBotRatio = filteredScans.length
      ? (filteredScans.reduce((sum, scan) => sum + (scan.bot_ratio || 0), 0) / filteredScans.length) * 100
      : null;

    return [
      {
        title: 'Bots Detected',
        value: String(totalBots),
        change: filteredScans.length ? `Across ${filteredScans.length} filtered scans` : 'No scans yet',
        changeColor: 'text-muted-foreground',
        icon: Network,
        color: 'text-destructive',
        borderColor: 'border-destructive/30',
        bgColor: 'bg-destructive/10',
      },
      {
        title: 'Active Networks',
        value: String(uniqueHashtags),
        change: filteredScans.length ? 'Unique hashtags in view' : 'No data available',
        changeColor: 'text-muted-foreground',
        icon: Network,
        color: 'text-warning',
        borderColor: 'border-warning/30',
        bgColor: 'bg-warning/10',
      },
      {
        title: 'Tweets Analyzed',
        value: String(totalTweets),
        change: filteredScans.length ? 'From hashtag-based scans' : 'Start your first scan',
        changeColor: 'text-muted-foreground',
        icon: TrendingUp,
        color: 'text-primary',
        borderColor: 'border-primary/30',
        bgColor: 'bg-primary/10',
      },
      {
        title: 'Average Bot Ratio',
        value: avgBotRatio === null ? '--' : `${avgBotRatio.toFixed(1)}%`,
        change: filteredScans.length ? 'Mean bot ratio across scans' : 'No data yet',
        changeColor: 'text-muted-foreground',
        icon: BarChart3,
        color: 'text-success',
        borderColor: 'border-success/30',
        bgColor: 'bg-success/10',
      },
    ];
  }, [filteredScans]);

  const reportInsights = useMemo(() => {
    if (!filteredScans.length) return [];

    const topScan = filteredScans[0];
    const topSuspicious = topScan?.top_suspicious_accounts?.[0];
    const highestRatioScan = [...filteredScans].sort((a, b) => (b.bot_ratio || 0) - (a.bot_ratio || 0))[0];
    const averageBotRatio = (
      (filteredScans.reduce((sum, scan) => sum + (scan.bot_ratio || 0), 0) / filteredScans.length) * 100
    ).toFixed(1);

    const insights = [
      `Overview: ${activeHashtagLabel} | ${activeWindowLabel} | minimum bot ratio ${minBotRatio}%`,
      `Included scans: ${filteredScans.length}`,
      `Average bot ratio: ${averageBotRatio}%`,
      highestRatioScan
        ? `Highest bot ratio: #${highestRatioScan.hashtag} at ${((highestRatioScan.bot_ratio || 0) * 100).toFixed(1)}%`
        : 'Highest bot ratio: no scan data available',
      topScan
        ? `Latest scan: #${topScan.hashtag} with ${topScan.bots_detected || 0} bots from ${topScan.analyzed_accounts || 0} accounts`
        : 'Latest scan: unavailable',
    ];

    if (topSuspicious) {
      insights.push(
        `Top suspicious account: @${topSuspicious.username} (${((topSuspicious.bot_probability || 0) * 100).toFixed(1)}% bot probability)`
      );
    }

    if (filteredScans.length > 1) {
      insights.push(
        `Trend: ${filteredScans[0].bot_ratio >= filteredScans[filteredScans.length - 1].bot_ratio ? 'bot activity is holding or increasing' : 'bot activity is easing'} in the selected view.`
      );
    }

    return insights;
  }, [activeHashtagLabel, activeWindowLabel, filteredScans, minBotRatio]);

  const exportReportPDF = async () => {
    if (!dashboardReportRef.current) return;

    const canvas = await html2canvas(dashboardReportRef.current, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#0a0e27',
    });

    const imageData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();

    const imgWidth = pdfWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imageData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pdfHeight;

    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imageData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pdfHeight;
    }

    pdf.addPage();

    const marginX = 14;
    const marginY = 16;
    const lineHeight = 7;

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(18);
    pdf.setTextColor(15, 23, 42);
    pdf.text('BotHunter Hashtag Scan Report', marginX, marginY);

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(10);
    pdf.setTextColor(71, 85, 105);
    pdf.text(`Generated: ${new Date().toLocaleString()}`, marginX, marginY + 8);

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(13);
    pdf.setTextColor(0, 153, 204);
    pdf.text('Overview', marginX, marginY + 18);

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(10);
    pdf.setTextColor(51, 65, 85);

    const insightLines = reportInsights.length
      ? reportInsights
      : ['No scans available for the selected filters. Run a hashtag scan to generate insights.'];

    let cursorY = marginY + 26;
    insightLines.forEach((line) => {
      const wrappedLines = pdf.splitTextToSize(`• ${line}`, pdfWidth - marginX * 2);
      wrappedLines.forEach((wrappedLine) => {
        if (cursorY > pdfHeight - 20) {
          pdf.addPage();
          cursorY = marginY;

          pdf.setFont('helvetica', 'normal');
          pdf.setFontSize(10);
          pdf.setTextColor(51, 65, 85);
        }
        pdf.text(wrappedLine, marginX, cursorY);
        cursorY += lineHeight;
      });
      cursorY += 2;
    });

    pdf.save(`bothunter-report-${new Date().toISOString().slice(0, 19)}.pdf`);
  };

  return (
    <div className="min-h-screen bg-background cyber-grid">
      <Navbar />

      <div
        className={`sticky top-16 z-40 border-b border-border/50 bg-background/80 backdrop-blur-xl transition-transform duration-300 will-change-transform ${
          headerVisible ? 'translate-y-0' : '-translate-y-full'
        }`}
      >
        <div className="container mx-auto px-4">
          <div className="flex min-h-16 py-3 items-center justify-between gap-3 flex-wrap">
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-foreground">Detection Dashboard</h1>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Last updated: {latestScan ? formatTimeAgo(latestScan.scanned_at) : 'No scans yet'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" className="gap-1.5 whitespace-nowrap text-xs sm:text-sm px-2.5 sm:px-3" onClick={exportReportPDF} disabled={!scans.length}>
                <Download className="h-4 w-4 flex-shrink-0" />
                <span>Export PDF</span>
              </Button>
              <Button variant="hero" size="sm" className="gap-1.5 whitespace-nowrap text-xs sm:text-sm px-3 sm:px-4" onClick={() => navigate('/new-scan')}>
                <Search className="h-4 w-4 flex-shrink-0" />
                <span>NEW SCAN</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div ref={dashboardReportRef} className="container mx-auto px-4 py-8">
        <Card glow className="p-5 mb-8 border border-primary/20 relative">
          <div className="flex items-start justify-between gap-4 mb-4 flex-wrap">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Dashboard Filters</p>
              <h2 className="text-xl font-semibold text-foreground">Refine the view</h2>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium mb-2 text-foreground">Hashtag</label>
              <select
                value={selectedHashtag}
                onChange={(e) => setSelectedHashtag(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-input border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">All hashtags</option>
                {availableHashtags.map((hashtag) => (
                  <option key={hashtag} value={hashtag}>
                    #{hashtag}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-foreground">Scan Window</label>
              <select
                value={scanWindow}
                onChange={(e) => setScanWindow(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-input border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">All scans</option>
                <option value="5">Latest 5 scans</option>
                <option value="10">Latest 10 scans</option>
                <option value="20">Latest 20 scans</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-foreground">Minimum Bot Ratio: {minBotRatio}%</label>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={minBotRatio}
                onChange={(e) => setMinBotRatio(Number(e.target.value))}
                className="w-full accent-cyan-400"
              />
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={() => {
                  setSelectedHashtag('all');
                  setScanWindow('all');
                  setMinBotRatio(0);
                }}
              >
                Reset Filters
              </Button>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span className="px-3 py-1 rounded-full bg-secondary/40 border border-border">{activeHashtagLabel}</span>
            <span className="px-3 py-1 rounded-full bg-secondary/40 border border-border">{activeWindowLabel}</span>
            <span className="px-3 py-1 rounded-full bg-secondary/40 border border-border">Min bot ratio {minBotRatio}%</span>
          </div>
        </Card>

        <Card glow className="p-6 mb-8 border border-secondary/20 relative">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Last Scan Summary</p>
              <h2 className="text-2xl font-semibold text-foreground">
                {latestScan ? `#${latestScan.hashtag}` : 'No scan available yet'}
              </h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full sm:w-auto">
              <div className="px-4 py-3 rounded-lg bg-secondary/30 border border-border min-w-[160px]">
                <p className="text-xs text-muted-foreground">Bot Ratio</p>
                <p className="text-xl font-bold text-foreground">
                  {latestScan ? `${((latestScan.bot_ratio || 0) * 100).toFixed(1)}%` : '--'}
                </p>
              </div>
              <div className="px-4 py-3 rounded-lg bg-secondary/30 border border-border min-w-[160px]">
                <p className="text-xs text-muted-foreground">Suspicious Accounts</p>
                <p className="text-xl font-bold text-foreground">{latestSuspiciousCount}</p>
              </div>
              <div className="px-4 py-3 rounded-lg bg-secondary/30 border border-border min-w-[160px]">
                <p className="text-xs text-muted-foreground">Scanned</p>
                <p className="text-xl font-bold text-foreground">
                  {latestScan ? formatTimeAgo(latestScan.scanned_at) : 'Never'}
                </p>
              </div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} glow className={`p-6 border relative ${stat.borderColor}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl ${stat.bgColor} ${stat.color}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                </div>
                <div className={`text-3xl font-bold font-mono mb-1 ${stat.color}`}>{stat.value}</div>
                <div className="text-sm text-muted-foreground mb-2">{stat.title}</div>
                <div className={`text-xs ${stat.changeColor}`}>{stat.change}</div>
              </Card>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card glow className="lg:col-span-2 min-h-[360px] relative">
            <div className="p-6 h-full">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Bot Ratio Trend</h2>
                </div>
                <CardInfoTag label="Line chart showing how the bot ratio changes across your saved hashtag scans." />
              </div>
              {noResultsForFilters ? (
                <EmptyState
                  title="No trend data for these filters"
                  description="Try a different hashtag, widen the scan window, or lower the minimum bot ratio to see the trend again."
                />
              ) : trendData.length ? (
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="name" stroke="#94a3b8" tick={{ fill: '#cbd5e1' }} />
                      <YAxis stroke="#94a3b8" tick={{ fill: '#cbd5e1' }} unit="%" domain={[0, 100]} />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        labelStyle={tooltipTextStyle}
                        itemStyle={tooltipTextStyle}
                        formatter={(value) => `${value}%`}
                        labelFormatter={(_, payload) => payload?.[0]?.payload?.hashtag || ''}
                      />
                      <Legend wrapperStyle={tooltipTextStyle} />
                      <Line
                        type="monotone"
                        dataKey="botRatio"
                        name="Bot Ratio"
                        stroke="#ff4757"
                        strokeWidth={3}
                        dot={{ r: 3 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No scans yet" description="Run your first hashtag scan to populate the trend chart." />
              )}
            </div>
          </Card>

          <Card glow className="min-h-[360px] relative">
            <div className="p-6 h-full">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Hashtag Risk Ranking</h2>
                </div>
                <CardInfoTag label="Ranks hashtags by average bot ratio so you can quickly spot the riskiest topics." />
              </div>
              {noResultsForFilters ? (
                <EmptyState
                  title="No ranking data for these filters"
                  description="Change the hashtag filter or reset the sliders to bring back the ranking chart."
                />
              ) : rankingData.length ? (
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rankingData} layout="vertical" margin={{ top: 4, right: 10, left: 20, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#cbd5e1' }} unit="%" domain={[0, 100]} />
                      <YAxis type="category" dataKey="hashtag" stroke="#94a3b8" tick={{ fill: '#cbd5e1' }} width={90} />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        labelStyle={tooltipTextStyle}
                        itemStyle={tooltipTextStyle}
                        formatter={(value) => `${value}%`}
                      />
                      <Bar dataKey="avgBotRatio" name="Avg Bot Ratio" radius={[0, 6, 6, 0]}>
                        {rankingData.map((entry, index) => (
                          <Cell key={`cell-${entry.hashtag}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No scans yet" description="Run a scan to see hashtag risk ranking here." />
              )}
            </div>
          </Card>

          <Card glow className="min-h-[360px] relative">
            <div className="p-6 h-full">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Bot vs Human Donut</h2>
                </div>
                <CardInfoTag label="Shows the total bot and human counts across the scans currently visible on the dashboard." />
              </div>
              {noResultsForFilters ? (
                <EmptyState
                  title="No composition data for these filters"
                  description="Adjust the filters to show the bot vs human breakdown for matching scans."
                />
              ) : compositionData.some((item) => item.value > 0) ? (
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} />
                      <Legend wrapperStyle={tooltipTextStyle} />
                      <Pie
                        data={compositionData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={85}
                        paddingAngle={3}
                      >
                        {compositionData.map((entry, index) => (
                          <Cell key={`slice-${entry.name}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No scans yet" description="Run a hashtag scan to populate the donut chart." />
              )}
            </div>
          </Card>

          <Card glow className="relative">
            <div className="p-6">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-warning" />
                  <h2 className="text-lg font-semibold">Recent Detections</h2>
                </div>
                <CardInfoTag label="Lists the most suspicious accounts from the latest matching scan, with their bot probability." />
              </div>
              {noResultsForFilters ? (
                <EmptyState
                  title="No recent detections for these filters"
                  description="Try resetting the filters or scanning a different hashtag to see suspicious accounts here."
                />
              ) : recentDetections.length > 0 ? (
                <div className="space-y-4">
                  {recentDetections.map((detection, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-4 p-4 rounded-lg bg-secondary/50 border border-border/50 hover:bg-secondary transition-colors"
                    >
                      <div className="p-2 rounded-lg bg-primary/10 border border-primary/30">
                        <Network className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="font-semibold">{detection.username}</span>
                          <span className="px-2 py-0.5 rounded text-xs bg-primary/10 text-primary border border-primary/30">
                            {detection.type}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Circle className={`h-2 w-2 ${detection.dotColor}`} fill="currentColor" />
                          <span className={detection.riskColor}>{detection.risk}</span>
                          <span className="text-muted-foreground">• {detection.time}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No detections yet" description="Start a new scan to detect bot activity and populate this list." />
              )}
            </div>
          </Card>

          <Card glow className="relative">
            <div className="p-6">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Activity Timeline</h2>
                </div>
              </div>
              {noResultsForFilters ? (
                <EmptyState
                  title="No activity for these filters"
                  description="Pick a different hashtag or reset filters to bring the timeline back."
                />
              ) : activityTimeline.length > 0 ? (
                <div className="space-y-4">
                  {activityTimeline.map((activity, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <Circle className={`h-3 w-3 mt-1.5 ${activity.color}`} fill="currentColor" />
                      <div>
                        <div className="font-semibold text-sm mb-1">{activity.time}</div>
                        <div className="text-sm text-muted-foreground">{activity.event}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No activity yet" description="Run your first scan and the timeline will appear here." />
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
