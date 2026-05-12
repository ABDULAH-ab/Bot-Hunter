import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Shield, TrendingUp, Users, Zap, Target, ArrowRight, Sparkles } from 'lucide-react';
import Navbar from '../components/Navbar';
import Button from '../components/ui/button';
import Card from '../components/ui/card';
import { useAuth } from '../context/AuthContext';

const Homepage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const features = [
    {
      icon: <Search className="h-8 w-8 text-primary" />,
      title: "Hashtag Analysis",
      description: "Scan any hashtag or trend to detect bot activity and fake engagement patterns"
    },
    {
      icon: <Shield className="h-8 w-8 text-secondary" />,
      title: "Bot Detection",
      description: "Advanced AI algorithms identify suspicious accounts and automated behavior"
    },
    {
      icon: <TrendingUp className="h-8 w-8 text-cyan-500" />,
      title: "Real-time Insights",
      description: "Get instant analytics on engagement rates, bot percentages, and authenticity scores"
    },
    {
      icon: <Users className="h-8 w-8 text-purple-500" />,
      title: "User Profiling",
      description: "Deep dive into user accounts to verify authenticity and detect patterns"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 cyber-grid">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent"></div>
        
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            {/* Welcome Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/30 mb-6">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm text-primary">Welcome back, {user?.username}!</span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text text-transparent animate-gradient">
              Hunt Down Social Media Bots
            </h1>
            
            <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
              Analyze hashtags, detect bot activity, and uncover fake engagement with our 
              <span className="text-primary font-semibold"> AI-powered detection system</span>. 
              Get real-time insights and protect your brand from artificial manipulation.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={() => navigate('/new-scan')}
                size="lg"
                className="gap-2 text-lg px-8 py-6"
              >
                <Search className="h-5 w-5" />
                Start New Scan
                <ArrowRight className="h-5 w-5" />
              </Button>
              
              <Button
                onClick={() => navigate('/dashboard')}
                variant="outline"
                size="lg"
                className="gap-2 text-lg px-8 py-6"
              >
                <TrendingUp className="h-5 w-5" />
                View Dashboard
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-background/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4 text-foreground">
              Powerful Bot Detection Features
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Leverage cutting-edge AI technology to identify and analyze bot activity across social media platforms
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card 
                key={index} 
                glow
                className="p-6 hover:scale-105 transition-transform duration-300 cursor-pointer group"
              >
                <div className="mb-4 p-3 rounded-lg bg-accent/50 w-fit group-hover:bg-accent transition-colors">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-2 text-foreground">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4 text-foreground">
                How It Works
              </h2>
              <p className="text-xl text-muted-foreground">
                Three simple steps to uncover bot activity
              </p>
            </div>

            <div className="space-y-8">
              <div className="flex gap-6 items-start">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center text-primary font-bold text-xl">
                  1
                </div>
                <div>
                  <h3 className="text-2xl font-semibold mb-2 text-foreground">Enter a Hashtag or Trend</h3>
                  <p className="text-muted-foreground text-lg">
                    Simply type in the hashtag, trending topic, or username you want to analyze. Our system works with Twitter, Instagram, and more.
                  </p>
                </div>
              </div>

              <div className="flex gap-6 items-start">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-secondary/20 border-2 border-secondary flex items-center justify-center text-secondary font-bold text-xl">
                  2
                </div>
                <div>
                  <h3 className="text-2xl font-semibold mb-2 text-foreground">AI Analysis in Action</h3>
                  <p className="text-muted-foreground text-lg">
                    Our advanced machine learning algorithms scan thousands of posts, accounts, and engagement patterns to detect suspicious activity.
                  </p>
                </div>
              </div>

              <div className="flex gap-6 items-start">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-cyan-500/20 border-2 border-cyan-500 flex items-center justify-center text-cyan-500 font-bold text-xl">
                  3
                </div>
                <div>
                  <h3 className="text-2xl font-semibold mb-2 text-foreground">Get Detailed Insights</h3>
                  <p className="text-muted-foreground text-lg">
                    Receive comprehensive reports showing bot percentages, suspicious accounts, engagement authenticity, and actionable recommendations.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-12 text-center">
              <Button
                onClick={() => navigate('/new-scan')}
                size="lg"
                className="gap-2"
              >
                <Zap className="h-5 w-5" />
                Try It Now
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-secondary/10 to-primary/10"></div>
        
        <div className="container mx-auto px-4 relative z-10">
          <Card glow className="max-w-4xl mx-auto p-12 text-center">
            <Target className="h-16 w-16 text-primary mx-auto mb-6" />
            <h2 className="text-4xl font-bold mb-4 text-foreground">
              Ready to Hunt Bots?
            </h2>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Start analyzing hashtags and trends right now. Uncover hidden bot networks and protect your social media presence.
            </p>
            <Button
              onClick={() => navigate('/new-scan')}
              size="lg"
              className="gap-2 text-lg px-8 py-6"
            >
              <Search className="h-6 w-6" />
              Start Your First Scan
              <ArrowRight className="h-6 w-6" />
            </Button>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default Homepage;
