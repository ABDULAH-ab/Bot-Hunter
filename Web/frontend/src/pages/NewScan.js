import React, { useEffect, useState } from 'react';
import { ArrowRight, Loader2, Sparkles, Target } from 'lucide-react';
import axios from 'axios';
import Navbar from '../components/Navbar';
import Button from '../components/ui/button';
import Card from '../components/ui/card';
import { API_URL } from '../config/auth.config';
import { useNavigate } from 'react-router-dom';

const defaultForm = {
  username: '',
};

const NewScan = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [hashtag, setHashtag] = useState('');
  const [hashtagLoading, setHashtagLoading] = useState(false);
  const [hashtagError, setHashtagError] = useState('');
  const [hashtagResult, setHashtagResult] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('hashtag'); // 'manual' or 'hashtag'

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const cleanedUsername = (form.username || '').trim().replace(/^@+/, '');
      if (!cleanedUsername) {
        throw new Error('Please enter a valid @username');
      }

      const response = await axios.get(`${API_URL}/predict/from-mongodb`, {
        params: {
          username: cleanedUsername,
          collection: 'User_Cache',
          use_scrape_cluster: true,
        },
      });

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to score the profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const runHashtagScan = async (rawTag) => {
    setHashtagLoading(true);
    setHashtagError('');
    setHashtagResult(null);

    try {
      const cleanTag = (rawTag || '').trim().replace(/^#/, '');
      if (!cleanTag) {
        throw new Error('Please enter a hashtag');
      }

      const response = await axios.get(`${API_URL}/predict/hashtag`, {
        params: { tag: cleanTag, max_accounts: 100, top_k: 10 },
      });
      setHashtagResult(response.data);
      setHashtag(cleanTag);

      // Persist scans so Dashboard can show hashtag results.
      try {
        const storageKey = 'bothunter_hashtag_scans';
        const currentScans = JSON.parse(localStorage.getItem(storageKey) || '[]');
        const entry = {
          ...response.data,
          scanned_at: new Date().toISOString(),
        };

        localStorage.setItem(storageKey, JSON.stringify([entry, ...currentScans].slice(0, 50)));
      } catch (storageError) {
        // Non-blocking: scan UI should still work even if storage is unavailable.
      }

      navigate('/dashboard');
    } catch (err) {
      setHashtagError(err.response?.data?.detail || err.message || 'Failed to analyze hashtag.');
    } finally {
      setHashtagLoading(false);
    }
  };

  const handleHashtagScan = async (event) => {
    event.preventDefault();
    await runHashtagScan(hashtag);
  };

  const loadSuggestions = async () => {
    setSuggestionsLoading(true);
    try {
      const response = await axios.get(`${API_URL}/predict/hashtag-suggestions`, {
        params: { limit: 4 },
      });
      setSuggestions(response.data?.suggestions || []);
    } catch (err) {
      setSuggestions([]);
    } finally {
      setSuggestionsLoading(false);
    }
  };

  useEffect(() => {
    loadSuggestions();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/30 mb-6">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm text-primary">Live Model Inference</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text text-transparent">
              Bot Detection Scan
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto">
              Use hashtag-based bot activity detection.
            </p>
          </div>

          {/* Tab Toggle */}
          <div className="flex justify-center gap-2 mb-10">
            <button
              onClick={() => setActiveTab('hashtag')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                activeTab === 'hashtag'
                  ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/50'
                  : 'bg-input border border-border text-muted-foreground hover:border-primary'
              }`}
            >
              <Target className="h-4 w-4 inline mr-2" />
              Hashtag Activity Scan
            </button>
          </div>

          {/* Hashtag Scan Section */}
          {activeTab === 'hashtag' && (
            <Card glow className="p-6 mb-8">
              <form onSubmit={handleHashtagScan} className="space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <Target className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-semibold text-foreground">Hashtag Bot Activity Scan</h2>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-muted-foreground">Hashtags</p>
                    <button
                      type="button"
                      onClick={loadSuggestions}
                      className="text-xs text-primary hover:underline"
                      disabled={suggestionsLoading}
                    >
                      {suggestionsLoading ? 'Refreshing...' : 'Refresh suggestions'}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.length ? (
                      suggestions.map((item) => (
                        <button
                          key={`${item.tag}-${item.last_scraped || ''}`}
                          type="button"
                          className="px-3 py-1.5 rounded-full border border-primary/40 bg-primary/10 text-primary text-xs hover:bg-primary/20 transition-colors"
                          onClick={() => runHashtagScan(item.tag)}
                          disabled={hashtagLoading}
                          title={`Tweets: ${item.tweets || 0}${item.last_scraped ? ` • Updated: ${item.last_scraped}` : ''}`}
                        >
                          #{item.tag}
                        </button>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">No suggestions yet.</span>
                    )}
                  </div>
                </div>

                <div className="flex flex-col md:flex-row gap-3">
                  <input
                    type="text"
                    value={hashtag}
                    onChange={(e) => setHashtag(e.target.value)}
                    placeholder="#Enter hashtag"
                    className="flex-1 px-4 py-3 rounded-lg bg-input border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <Button type="submit" className="gap-2" disabled={hashtagLoading}>
                    {hashtagLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        Analyze Hashtag
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </Button>
                </div>

                {hashtagError ? (
                  <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive">
                    {hashtagError}
                  </div>
                ) : null}

                {hashtagResult ? (
                  <div className="space-y-4 pt-2">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="p-3 rounded-lg bg-secondary/20 border border-border">
                        <p className="text-xs text-muted-foreground">Hashtag</p>
                        <p className="text-lg font-semibold text-foreground">#{hashtagResult.hashtag}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-secondary/20 border border-border">
                        <p className="text-xs text-muted-foreground">Accounts Analyzed</p>
                        <p className="text-lg font-semibold text-foreground">{hashtagResult.analyzed_accounts}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-secondary/20 border border-border">
                        <p className="text-xs text-muted-foreground">Bots Detected</p>
                        <p className="text-lg font-semibold text-destructive">{hashtagResult.bots_detected}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-secondary/20 border border-border">
                        <p className="text-xs text-muted-foreground">Bot Ratio</p>
                        <p className="text-lg font-semibold text-foreground">{(hashtagResult.bot_ratio * 100).toFixed(1)}%</p>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-warning/10 border border-warning/30 text-sm text-muted-foreground">
                      {hashtagResult.note}
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold mb-2 text-foreground">Top Suspicious Accounts</h3>
                      <div className="space-y-2">
                        {hashtagResult.top_suspicious_accounts?.length ? (
                          hashtagResult.top_suspicious_accounts.map((item, index) => (
                            <div key={`${item.username}-${index}`} className="p-3 rounded-lg bg-secondary/20 border border-border flex items-center justify-between gap-3">
                              <div>
                                <p className="font-medium text-foreground">@{item.username}</p>
                                <p className="text-xs text-muted-foreground">Label: {item.label.toUpperCase()} • Tweets used: {item.tweets_used}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground">Bot Probability</p>
                                <p className="font-semibold text-destructive">{(item.bot_probability * 100).toFixed(1)}%</p>
                              </div>
                            </div>
                          ))
                        ) : (
                          <p className="text-sm text-muted-foreground">No account-level results available.</p>
                        )}
                      </div>
                    </div>
                  </div>
                ) : null}
              </form>
            </Card>
          )}

          {/* Manual Scan Section */}
          {activeTab === 'manual' && (
            <>
              <div className="space-y-6 max-w-4xl mx-auto">
                <Card glow className="p-8">
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">Username</label>
                      <input
                        type="text"
                        value={form.username}
                        onChange={(e) => updateField('username', e.target.value)}
                        className="w-full px-4 py-3 rounded-lg bg-input border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                        placeholder="@username"
                        required
                      />
                      <p className="mt-2 text-xs text-muted-foreground">
                        Enter only the handle (for example: @jack). Profile features will be fetched automatically from MongoDB.
                      </p>
                    </div>

                {error && (
                  <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive">
                    {error}
                  </div>
                )}

                <Button type="submit" size="lg" className="w-full gap-2 text-lg py-6" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Looking up and scoring...
                    </>
                  ) : (
                    <>
                      <Target className="h-5 w-5" />
                      Run Bot Detection
                      <ArrowRight className="h-5 w-5" />
                    </>
                  )}
                </Button>
              </form>
            </Card>

                {result ? (
                  <Card glow className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Prediction</p>
                        <h2 className={`text-3xl font-bold ${result.label === 'bot' ? 'text-destructive' : 'text-secondary'}`}>
                          {result.label.toUpperCase()}
                        </h2>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">Confidence</p>
                        <p className="text-2xl font-bold text-foreground">{(result.confidence * 100).toFixed(2)}%</p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Human</span>
                          <span>{(result.human_probability * 100).toFixed(2)}%</span>
                        </div>
                        <div className="h-3 rounded-full bg-muted overflow-hidden">
                          <div className="h-full bg-secondary" style={{ width: `${result.human_probability * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Bot</span>
                          <span>{(result.bot_probability * 100).toFixed(2)}%</span>
                        </div>
                        <div className="h-3 rounded-full bg-muted overflow-hidden">
                          <div className="h-full bg-destructive" style={{ width: `${result.bot_probability * 100}%` }} />
                        </div>
                      </div>

                      {result.signals?.length ? (
                        <div>
                          <h3 className="text-sm font-semibold mb-2 text-foreground">Signals</h3>
                          <ul className="space-y-2 text-sm text-muted-foreground">
                            {result.signals.map((signal, index) => (
                              <li key={index}>• {signal}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  </Card>
                ) : null}
          </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewScan;