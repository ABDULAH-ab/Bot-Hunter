import React from 'react';
import Navbar from '../components/Navbar';
import Card from '../components/ui/card';

const Terms = () => {
  return (
    <div className="min-h-screen bg-background cyber-grid">
      <Navbar />
      <div className="container mx-auto px-4 py-20 max-w-4xl">
        <Card glow className="p-8 md:p-12 backdrop-blur-xl">
          <h1 className="text-3xl md:text-4xl font-bold mb-6 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Terms of Service
          </h1>
          <p className="text-xs text-muted-foreground mb-8">Last Updated: May 2026</p>

          <div className="space-y-6 text-sm md:text-base text-muted-foreground leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-foreground mb-2">1. Acceptance of Terms</h2>
              <p>
                By accessing and using the Bot-Hunter application ("Platform"), you accept and agree to be bound by the terms and provisions of this agreement. The platform is intended for academic research, journalism, and public social media verification analysis.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-foreground mb-2">2. Description of Service</h2>
              <p>
                Bot-Hunter provides automated machine learning diagnostics to estimate the likelihood of social media accounts behaving as automated entities (bots) on Twitter/X. Results are provided purely as predictive estimates driven by Relational Graph Convolutional Networks (RGCN) and BERTweet textual encodings.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-foreground mb-2">3. Ethical and Acceptable Use</h2>
              <p>
                You agree not to misuse the Platform services. Specifically, you agree not to:
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1 text-slate-300">
                <li>Attempt to reverse-engineer model endpoint vectors or disrupt internal database scraping queues.</li>
                <li>Utilize prediction confidence outputs for systematic user harassment, targeted public defamation, or automated API re-broadcasting without authorization.</li>
                <li>Submit un-sanitized continuous payload requests designed to exhaust server hardware rate-limiting burst allowances.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-foreground mb-2">4. Disclaimer of Warranties</h2>
              <p>
                The Platform is provided on an "as is" and "as available" basis. Machine learning classification models inherently produce false positive and false negative variations based on temporal data shifts. The owners and university affiliates assume no legal accountability for downstream verification actions derived from these automated reports.
              </p>
            </section>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Terms;
