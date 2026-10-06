import React, { useState, useEffect, useRef, FormEvent } from "react";
import { askQuestion, Citation } from "../Common/articleReader";
import "./ArticleViewer.css";

export interface ArticleData {
  url?: string;
  title?: string;
  category?: string;
  level?: string;
  difficulty?: string;
  summary: string;
  main_idea: string;
  key_insights: string[];
  important_concepts: string[];
  practical_takeaways: string[];
}


const DEFAULT_DATA: ArticleData = {
  url: "https://psyche.co/guides/how-to-rediscover-your-purpose-later-in-life",
  title: "How to rediscover your purpose later in life",
  category: "Psyche Guides",
  level: "Beginner",
  summary:
    "Many older adults experience a subtle, unacknowledged sense of dissatisfaction or loss of direction despite being active and outwardly engaged. Popular cultural advice urging people to 'reinvent' themselves in later life can add undue pressure and feel misaligned with evolving psychological needs. Drawing on psychological frameworks such as Laura Carstensen's socioemotional selectivity theory and Erik Erikson's developmental task of integration, this article proposes 'reorientation' as a more adaptive path. Reorientation focuses on examining existing commitments, listening to personal energy patterns, deepening core strengths, and reframing contributions to align with an integrated sense of self.",
  main_idea:
    "Finding purpose in later life is not about dramatic reinvention but rather about 'reorientation' – a reflective process of aligning one's activities and contributions with evolving values, emotional depth, and a more integrated sense of self.",
  key_insights: [
    "Later-life malaise is common and distinct from depression: Many active older adults experience a subtle sense of dissatisfaction or loss of direction that is not clinical depression, but a sign that old routines no longer align.",
    "Reinvention narratives can be counterproductive: Popular messages promoting 'second acts' or total self-reinvention create artificial pressure and conflict with natural developmental needs.",
    "Development shifts from novelty to depth: Carstensen's socioemotional selectivity theory shows that as time horizons shorten, priorities naturally shift toward emotional depth, meaningful relationships, and shared wisdom over broad exploration.",
    "Integration is the primary developmental task: Erik Erikson highlighted that later adulthood centers on integrating past experiences into a coherent self rather than discarding existing identities.",
    "Energy serves as an essential compass: Differentiating between energizing effort and draining exhaustion helps identify where commitments need realignment.",
    "Contribution evolves beyond visible achievement: Value in later life often shifts from external status to sharing wisdom, mentoring, and offering a grounded presence.",
    "Reorientation is a gradual self-alignment: Rather than a sudden overhaul, reorientation is an intentional process of listening to internal cues and refining daily priorities."
  ],
  important_concepts: [
    "Later-Life Malaise",
    "Reinvention Narrative Critique",
    "Socioemotional Selectivity Theory",
    "Erikson's Task of Integration",
    "Reorientation Approach",
    "Energy Log",
    "Reframing Contribution"
  ],
  practical_takeaways: [
    "Evaluate commitments honestly: Assess current activities by asking 'Does this still feel alive to me?' to highlight obligations kept purely out of habit.",
    "Track energy patterns: Keep an 'energy log' for a week, recording which interactions and tasks leave you replenished vs. drained.",
    "Adjust personal boundaries: Use your energy log to set clearer boundaries around draining obligations and dedicate more time to energizing pursuits.",
    "Map existing strengths and values: List accumulated skills, consistent personal values, and meaningful experiences to discover new ways of expressing your authentic self.",
    "Prioritize depth over novelty: Instead of pursuing unrelated new fields, focus on deepening existing talents and passing on accumulated wisdom.",
    "Reframe contribution: Shift focus from 'what left to prove' to 'what wisdom is worth sharing', valuing mentorship and presence as key contributions.",
    "Embrace gradual tweaks over drastic overhauls: Focus on small, intentional shifts in your routine to foster long-term clarity and purpose."
  ]
};

export interface ArticleViewerProps {
  articleData?: ArticleData;
  onBack?: () => void;
}

const ArticleViewer: React.FC<ArticleViewerProps> = ({
  articleData,
  onBack,
}) => {
  const data = articleData || DEFAULT_DATA;
  const articleId = data.url || data.title || "default-article";

  // Theme State
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Audio / Speech State
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isPausedAudio, setIsPausedAudio] = useState(false);

  // Concept selection state
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);

  // Question & Reply state
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Article-specific practical takeaways done state
  const [done, setDone] = useState<number[]>([]);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(`ia-done-${articleId}`);
      setDone(saved ? JSON.parse(saved) : []);
    } catch {
      setDone([]);
    }
  }, [articleId]);

  useEffect(() => {
    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [articleId]);

  const toggleTheme = () => {
    setTheme((prevTheme) => {
      const nextTheme = prevTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      return nextTheme;
    });
  };

  const handlePlayAudio = () => {
    if (!("speechSynthesis" in window)) {
      alert("Text-to-speech is not supported in your browser.");
      return;
    }

    if (isPausedAudio) {
      window.speechSynthesis.resume();
      setIsPlayingAudio(true);
      setIsPausedAudio(false);
      return;
    }

    window.speechSynthesis.cancel();

    const textToRead = `${data.title}. Main Idea: ${data.main_idea}. Summary: ${data.summary}`;
    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      setIsPlayingAudio(false);
      setIsPausedAudio(false);
    };

    utterance.onerror = () => {
      setIsPlayingAudio(false);
      setIsPausedAudio(false);
    };

    window.speechSynthesis.speak(utterance);
    setIsPlayingAudio(true);
    setIsPausedAudio(false);
  };

  const handlePauseAudio = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.pause();
      setIsPlayingAudio(false);
      setIsPausedAudio(true);
    }
  };

  const handleStopAudio = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsPlayingAudio(false);
      setIsPausedAudio(false);
    }
  };

  const handleConceptClick = (concept: string) => {
    if (selectedConcept === concept) {
      setSelectedConcept(null);
      setQuestion("");
    } else {
      setSelectedConcept(concept);
      setQuestion(`Explain "${concept}" in simple terms`);
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  const handleTaskToggle = (index: number) => {
    const updatedDone = done.includes(index)
      ? done.filter((i) => i !== index)
      : [...done, index];
    setDone(updatedDone);
    try {
      localStorage.setItem(`ia-done-${articleId}`, JSON.stringify(updatedDone));
    } catch (e) {
      console.error(e);
    }
  };

  const executeAsk = async (qText: string) => {
    const q = qText.trim();
    if (!q || isAsking) return;

    setIsAsking(true);
    setReply("Thinking...");
    setCitations([]);

    try {
      const res = await askQuestion(q, {
        url: data.url,
        title: data.title,
      });
      setReply(res.answer);
      setCitations(res.citations || []);
    } catch (err) {
      setReply("Sorry, couldn't process your question at the moment. Please try again.");
      setCitations([]);
    } finally {
      setIsAsking(false);
    }
  };


  const handleAskSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await executeAsk(question);
  };

  const handleQuickAIAction = (promptText: string) => {
    setQuestion(promptText);
    executeAsk(promptText);
  };

  const totalTasks = data.practical_takeaways?.length || 0;
  const doneCount = done.length;
  const progressPercent = totalTasks > 0 ? (doneCount / totalTasks) * 100 : 0;

  return (
    <div className="article-viewer-root" data-theme={theme}>
      <main className="wrap">
        <nav className="top">
          {onBack ? (
            <button
              className="back-btn"
              type="button"
              onClick={onBack}
              aria-label="Back to dashboard"
            >
              ← Dashboard
            </button>
          ) : (
            <button
              className="back-btn"
              type="button"
              onClick={() => window.history.back()}
              aria-label="Back to dashboard"
            >
              ← Dashboard
            </button>
          )}
          <div className="nav-actions">
            {isPlayingAudio ? (
              <>
                <button className="audio-btn active" type="button" onClick={handlePauseAudio}>
                  ⏸ Pause
                </button>
                <button className="audio-btn stop" type="button" onClick={handleStopAudio}>
                  ⏹ Stop
                </button>
              </>
            ) : isPausedAudio ? (
              <>
                <button className="audio-btn active" type="button" onClick={handlePlayAudio}>
                  ▶ Resume
                </button>
                <button className="audio-btn stop" type="button" onClick={handleStopAudio}>
                  ⏹ Stop
                </button>
              </>
            ) : (
              <button className="audio-btn" type="button" onClick={handlePlayAudio} title="Listen to this article summary">
                🔊 Listen to article
              </button>
            )}
            <button id="theme" type="button" onClick={toggleTheme}>
              Theme
            </button>
          </div>
        </nav>

        <header>
          <h1 id="title">{data.title || "How to rediscover your purpose later in life"}</h1>
          <div className="meta">
            <span>{data.category || "Psyche Guides"}</span>
            <span className="level" id="level">
              {data.level || data.difficulty || "Beginner"}
            </span>
          </div>
        </header>

        {/* Quick AI Action Shortcuts */}
        <div className="ai-actions-row">
          <button
            type="button"
            className="ai-action-chip"
            onClick={() => handleQuickAIAction("Summarize the top 3 insights of this article in bullet points")}
          >
            ✨ Summarize Key Insights
          </button>
          <button
            type="button"
            className="ai-action-chip"
            onClick={() => handleQuickAIAction("Explain the central concept of this article in simple terms")}
          >
            💡 Explain Central Concept
          </button>
          <button
            type="button"
            className="ai-action-chip"
            onClick={() => handleQuickAIAction("How can I apply the practical takeaways of this article in my daily life?")}
          >
            🎯 How to Apply Takeaways
          </button>
        </div>

        <section className="idea" aria-labelledby="idea-h">
          <h2 id="idea-h">The main idea</h2>
          <p id="idea">{data.main_idea}</p>
        </section>

        <h2 className="sec">Summary</h2>
        <p className="summary" id="summary">
          {data.summary}
        </p>

        <h2 className="sec">Key insights</h2>
        <ul className="insights" id="insights">
          {data.key_insights?.map((insight, index) => (
            <li key={index}>{insight}</li>
          ))}
        </ul>

        <h2 className="sec">Concepts to know</h2>
        <p className="sub">Select a concept to focus it, then ask about it below.</p>
        <div className="chips" id="chips" role="group" aria-label="Concepts">
          {data.important_concepts?.map((concept) => {
            const isSelected = selectedConcept === concept;
            return (
              <button
                key={concept}
                type="button"
                className="chip"
                aria-pressed={isSelected}
                onClick={() => handleConceptClick(concept)}
              >
                {concept}
              </button>
            );
          })}
        </div>
        <p className="chip-note" id="chipnote" aria-live="polite">
          {selectedConcept ? `Asking about: ${selectedConcept}` : ""}
        </p>

        <h2 className="sec">Try it yourself</h2>
        <div className="prog">
          <div className="bar">
            <i id="barfill" style={{ width: `${progressPercent}%` }}></i>
          </div>
          <span id="count" aria-live="polite">
            {doneCount} of {totalTasks} tried
          </span>
        </div>
        <ul className="tasks" id="tasks">
          {data.practical_takeaways?.map((takeaway, index) => {
            const isChecked = done.includes(index);
            return (
              <li key={index}>
                <label>
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => handleTaskToggle(index)}
                  />
                  <span>{takeaway}</span>
                </label>
              </li>
            );
          })}
        </ul>
      </main>

      <div className="ask">
        {reply && (
          <div className="reply" id="reply" aria-live="polite">
            <div className="reply-header">
              <span>InsightAI Answer</span>
              <button
                type="button"
                className="reply-close"
                onClick={() => { setReply(""); setCitations([]); }}
                aria-label="Close answer"
              >
                ✕
              </button>
            </div>
            <div className="reply-body">{reply}</div>
            {citations && citations.length > 0 && (
              <div className="reply-citations" style={{ marginTop: "12px", borderTop: "1px solid rgba(128,128,128,0.2)", paddingTop: "8px" }}>
                <h4 style={{ fontSize: "12px", margin: "0 0 6px 0", opacity: 0.8 }}>Source Citations ({citations.length} retrieved):</h4>
                <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", opacity: 0.85 }}>
                  {citations.map((c, i) => (
                    <li key={i} style={{ marginBottom: "4px" }}>
                      <strong>[Chunk {c.chunk_index + 1}]</strong> ({Math.round(c.score * 100)}% match): "{c.text.slice(0, 140)}{c.text.length > 140 ? "..." : ""}"
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <form id="askform" onSubmit={handleAskSubmit}>
          <input
            ref={inputRef}
            id="q"
            type="text"
            placeholder="Ask about this article"
            aria-label="Ask a question about this article"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isAsking}
          />
          <button type="submit" disabled={isAsking}>
            {isAsking ? "Asking..." : "Ask"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ArticleViewer;
