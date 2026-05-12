import React from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  Shield,
  Activity,
  Network,
  FileText,
  Zap,
  ArrowRight,
  Search,
  BarChart3,
  AlertTriangle,
} from 'lucide-react';
import Button from '../components/ui/button';
import Card from '../components/ui/card';
import Navbar from '../components/Navbar';
import Logo from '../components/Logo';

const Landing = () => {
  const features = [
    {
      icon: Search,
      title: 'Real-Time Detection',
      description: 'Stream and analyze tweets in real-time using advanced ML models to identify bot-generated content.',
    },
    {
      icon: Network,
      title: 'Network Analysis',
      description: 'Detect coordinated bot networks through graph analytics and behavioral pattern recognition.',
    },
    {
      icon: BarChart3,
      title: 'Trend Monitoring',
      description: 'Track how bots influence trending topics and measure their impact on public discourse.',
    },
    {
      icon: AlertTriangle,
      title: 'Anomaly Detection',
      description: 'Identify unusual activity spikes and suspicious behavior patterns automatically.',
    },
    {
      icon: Activity,
      title: 'Live Dashboard',
      description: 'Visualize bot activities, suspicious trends, and influence patterns in real-time.',
    },
    {
      icon: FileText,
      title: 'One-Click Reports',
      description: 'Generate comprehensive PDF and CSV reports for easy sharing of findings.',
    },
  ];

  return (
    <div className="min-h-screen bg-background cyber-grid">
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-accent/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5 mb-8 animate-fade-in">
              <Zap className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-primary">AI-Powered Bot Detection</span>
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-7xl font-bold mb-6 animate-fade-in-delay-1">
              <span className="text-foreground">Hunt Down</span>
              <br />
              <span className="text-gradient">Social Media Bots</span>
            </h1>

            <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto animate-fade-in-delay-2">
              Detect, analyze, and expose automated accounts on X (Twitter) with cutting-edge
              machine learning and real-time monitoring.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-delay-3">
              <Link to="/signup">
                <Button variant="hero" size="xl" className="gap-2">
                  Start Hunting
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link to="/dashboard">
                <Button variant="outline" size="xl" className="gap-2">
                  <Activity className="h-5 w-5" />
                  View Dashboard
                </Button>
              </Link>
            </div>
          </div>

          {/* Hero Visual */}
          <div className="mt-20 relative max-w-5xl mx-auto">
            <Card glow className="p-8 bg-card/50 backdrop-blur-xl">
              <div className="grid grid-cols-3 gap-4">
                {/* Animated scan visualization */}
                <div className="col-span-2 aspect-video rounded-lg bg-secondary/50 relative overflow-hidden border border-border">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center space-y-4">
                      <Bot className="h-16 w-16 text-primary mx-auto animate-float" />
                      <div className="font-mono text-sm text-muted-foreground">
                        Scanning network traffic...
                      </div>
                    </div>
                  </div>
                  {/* Scan line effect */}
                  <div className="absolute inset-0 bg-gradient-to-b from-primary/20 via-primary/5 to-transparent animate-scan" />
                </div>

                {/* Stats sidebar */}
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                    <div className="text-2xl font-bold font-mono text-destructive">847</div>
                    <div className="text-xs text-muted-foreground">Bots Detected</div>
                  </div>
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                    <div className="text-2xl font-bold font-mono text-warning">23</div>
                    <div className="text-xs text-muted-foreground">Active Networks</div>
                  </div>
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                    <div className="text-2xl font-bold font-mono text-success">99.2%</div>
                    <div className="text-xs text-muted-foreground">Accuracy Rate</div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 relative">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Powerful <span className="text-gradient">Detection Tools</span>
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need to identify and analyze automated accounts affecting social
              media discourse.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card
                key={feature.title}
                glow
                className="p-6 group hover:-translate-y-1 transition-all duration-300"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="p-3 rounded-xl bg-primary/10 w-fit mb-4 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative">
        <div className="absolute inset-0 bg-gradient-to-t from-primary/5 to-transparent" />
        <div className="container mx-auto px-4 relative">
          <Card glow className="p-12 text-center bg-card/50 backdrop-blur-xl max-w-3xl mx-auto">
            <Shield className="h-16 w-16 text-primary mx-auto mb-6" />
            <h2 className="text-3xl font-bold mb-4">Ready to Protect the Truth?</h2>
            <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
              Join researchers, journalists, and analysts using Bot Hunter to expose automated
              influence campaigns.
            </p>
            <Link to="/signup">
              <Button variant="hero" size="xl" className="gap-2">
                Create Free Account
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-border/50">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <Logo size="small" />
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Bot Hunter. AI-powered bot detection for authenticity.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
