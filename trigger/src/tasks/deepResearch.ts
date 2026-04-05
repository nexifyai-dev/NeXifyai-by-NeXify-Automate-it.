/**
 * NeXifyAI — Deep Research Task
 * Multi-Layer Web Research mit rekursiver Query-Expansion.
 * Nutzt Exa AI für semantische Suche + DeepSeek/OpenAI für Synthese.
 */
import { task, metadata } from "@trigger.dev/sdk/v3";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import Exa from "exa-js";
import { z } from "zod";

const exa = new Exa(process.env.EXA_API_KEY!);

interface ResearchResult {
  query: string;
  sources: Array<{
    title: string;
    url: string;
    text: string;
    relevance: number;
  }>;
  synthesis: string;
  subQueries: string[];
}

export const deepResearchTask = task({
  id: "deep-research",
  maxDuration: 300,
  retry: { maxAttempts: 2 },
  run: async (payload: {
    initialQuery: string;
    depth?: number;
    breadth?: number;
    language?: string;
  }) => {
    const { initialQuery, depth = 2, breadth = 3, language = "de" } = payload;
    const allResults: ResearchResult[] = [];
    let totalSources = 0;

    metadata.set("status", "started");
    metadata.set("query", initialQuery);

    // Layer 1: Initial Search
    metadata.set("phase", "Layer 1: Initiale Suche");
    metadata.set("progress", 10);

    const initialResults = await searchAndSynthesize(initialQuery, language);
    allResults.push(initialResults);
    totalSources += initialResults.sources.length;

    metadata.set("sources_found", totalSources);
    metadata.set("progress", 30);

    // Layer 2+: Recursive Expansion
    if (depth >= 2 && initialResults.subQueries.length > 0) {
      metadata.set("phase", "Layer 2: Tiefenrecherche");

      const subQueries = initialResults.subQueries.slice(0, breadth);
      for (let i = 0; i < subQueries.length; i++) {
        metadata.set("sub_query", `${i + 1}/${subQueries.length}: ${subQueries[i]}`);
        metadata.set("progress", 30 + Math.round((i / subQueries.length) * 40));

        const subResult = await searchAndSynthesize(subQueries[i], language);
        allResults.push(subResult);
        totalSources += subResult.sources.length;
        metadata.set("sources_found", totalSources);
      }
    }

    // Final Synthesis
    metadata.set("phase", "Finale Synthese");
    metadata.set("progress", 80);

    const finalSynthesis = await generateText({
      model: openai("gpt-4o-mini"),
      prompt: `Erstelle eine umfassende Analyse basierend auf diesen Research-Ergebnissen.
      
Ursprüngliche Frage: ${initialQuery}
Sprache: ${language === "de" ? "Deutsch" : "English"}

Ergebnisse:
${allResults.map((r, i) => `--- Recherche ${i + 1}: ${r.query} ---\n${r.synthesis}\n`).join("\n")}

Erstelle eine strukturierte Zusammenfassung mit:
1. Kernerkenntnisse
2. Detailanalyse
3. Handlungsempfehlungen
4. Quellen-Bewertung`,
    });

    metadata.set("phase", "Abgeschlossen");
    metadata.set("progress", 100);
    metadata.set("status", "completed");

    return {
      query: initialQuery,
      layers: allResults.length,
      totalSources,
      results: allResults,
      finalSynthesis: finalSynthesis.text,
      completedAt: new Date().toISOString(),
    };
  },
});

async function searchAndSynthesize(query: string, language: string): Promise<ResearchResult> {
  // Exa semantic search
  const searchResults = await exa.searchAndContents(query, {
    type: "neural",
    numResults: 5,
    text: { maxCharacters: 3000 },
    highlights: true,
  });

  const sources = searchResults.results.map((r) => ({
    title: r.title || "",
    url: r.url,
    text: r.text || "",
    relevance: r.score || 0,
  }));

  // Synthesize with LLM
  const synthesis = await generateText({
    model: openai("gpt-4o-mini"),
    prompt: `Analysiere diese Suchergebnisse zu "${query}" (Sprache: ${language}):

${sources.map((s, i) => `[${i + 1}] ${s.title}\n${s.text.substring(0, 800)}\n`).join("\n")}

Erstelle:
1. Zusammenfassung der Kernpunkte
2. Widersprüche zwischen Quellen
3. 3 Vertiefungsfragen für weitere Recherche

Format: Strukturiert mit Überschriften.`,
  });

  // Extract sub-queries
  const subQueryExtract = await generateText({
    model: openai("gpt-4o-mini"),
    prompt: `Basierend auf dieser Analyse zu "${query}":
${synthesis.text.substring(0, 1500)}

Generiere exakt 3 spezifische Folgefragen für tiefere Recherche.
Antwort NUR als JSON-Array: ["Frage1", "Frage2", "Frage3"]`,
  });

  let subQueries: string[] = [];
  try {
    subQueries = JSON.parse(subQueryExtract.text);
  } catch {
    subQueries = [];
  }

  return { query, sources, synthesis: synthesis.text, subQueries };
}
