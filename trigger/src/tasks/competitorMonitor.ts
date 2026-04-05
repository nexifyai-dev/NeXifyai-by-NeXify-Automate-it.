/**
 * NeXifyAI — Competitor Monitor Task
 * Automatisches Release-Tracking und Wettbewerbsanalyse.
 */
import { task, metadata, schedules } from "@trigger.dev/sdk/v3";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY!);

interface CompetitorResult {
  competitor: string;
  url: string;
  changes: Array<{
    type: string;
    title: string;
    url: string;
    summary: string;
    date?: string;
    relevance: number;
  }>;
  analysis: string;
}

export const competitorMonitorTask = task({
  id: "competitor-monitor",
  maxDuration: 240,
  retry: { maxAttempts: 2 },
  run: async (payload: {
    competitors: Array<{ name: string; url: string; keywords?: string[] }>;
    lookbackDays?: number;
    language?: string;
  }) => {
    const { competitors, lookbackDays = 7, language = "de" } = payload;
    const results: CompetitorResult[] = [];

    metadata.set("status", "monitoring");
    metadata.set("competitors_total", competitors.length);

    for (let i = 0; i < competitors.length; i++) {
      const comp = competitors[i];
      metadata.set("current_competitor", comp.name);
      metadata.set("progress", Math.round((i / competitors.length) * 80));

      // Search for recent mentions and changes
      const queries = [
        `"${comp.name}" news updates ${new Date().getFullYear()}`,
        `${comp.url} new features releases`,
        ...(comp.keywords || []).map((kw) => `"${comp.name}" ${kw}`),
      ];

      const allSources: CompetitorResult["changes"] = [];

      for (const query of queries.slice(0, 3)) {
        try {
          const searchResults = await exa.searchAndContents(query, {
            type: "neural",
            numResults: 3,
            text: { maxCharacters: 1500 },
            startPublishedDate: new Date(
              Date.now() - lookbackDays * 24 * 60 * 60 * 1000
            ).toISOString().split("T")[0],
          });

          for (const r of searchResults.results) {
            allSources.push({
              type: "mention",
              title: r.title || "",
              url: r.url,
              summary: (r.text || "").substring(0, 500),
              date: r.publishedDate,
              relevance: r.score || 0,
            });
          }
        } catch {
          // Skip failed queries
        }
      }

      // Analyze changes
      if (allSources.length > 0) {
        const analysis = await generateText({
          model: openai("gpt-4o-mini"),
          prompt: `Analysiere die neuesten Aktivitäten von ${comp.name} (${comp.url}):

${allSources.map((s, i) => `[${i + 1}] ${s.title}\n${s.summary}\n`).join("\n")}

Erstelle auf ${language === "de" ? "Deutsch" : "English"}:
1. Zusammenfassung der wichtigsten Änderungen
2. Strategische Implikationen für uns (NeXifyAI)
3. Handlungsempfehlungen
4. Risikobewertung (1-10)`,
        });

        results.push({
          competitor: comp.name,
          url: comp.url,
          changes: allSources,
          analysis: analysis.text,
        });
      } else {
        results.push({
          competitor: comp.name,
          url: comp.url,
          changes: [],
          analysis: "Keine neuen Aktivitäten im Überwachungszeitraum gefunden.",
        });
      }
    }

    // Overall summary
    metadata.set("phase", "Gesamtanalyse");
    metadata.set("progress", 90);

    const overallSummary = await generateText({
      model: openai("gpt-4o-mini"),
      prompt: `Erstelle einen Gesamt-Wettbewerbsbericht (${language === "de" ? "Deutsch" : "English"}):

${results.map((r) => `## ${r.competitor}\n${r.analysis}\n`).join("\n")}

Erstelle:
1. Executive Summary (3 Sätze)
2. Wichtigste Marktbewegungen
3. Unsere strategische Position
4. Top-3-Handlungsempfehlungen`,
    });

    metadata.set("status", "completed");
    metadata.set("progress", 100);

    return {
      competitors: results,
      overallSummary: overallSummary.text,
      lookbackDays,
      monitoredAt: new Date().toISOString(),
      totalChangesFound: results.reduce((acc, r) => acc + r.changes.length, 0),
    };
  },
});

// Scheduled: Daily at 08:00 UTC
export const dailyCompetitorMonitor = schedules.task({
  id: "daily-competitor-monitor",
  cron: "0 8 * * *",
  run: async () => {
    // Default competitors - can be overridden via config
    const defaultCompetitors = [
      { name: "Octarine AI", url: "https://octarine.ai", keywords: ["AI agents", "automation"] },
    ];

    return await competitorMonitorTask.trigger({
      competitors: defaultCompetitors,
      lookbackDays: 1,
      language: "de",
    });
  },
});
