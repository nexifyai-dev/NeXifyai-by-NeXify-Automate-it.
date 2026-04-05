/**
 * NeXifyAI — Generate Report Task
 * HTML-Report-Generierung aus Research-Daten.
 */
import { task, metadata } from "@trigger.dev/sdk/v3";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

export const generateReportTask = task({
  id: "generate-report",
  maxDuration: 120,
  retry: { maxAttempts: 2 },
  run: async (payload: {
    title: string;
    content: string;
    format?: "html" | "markdown";
    language?: string;
    branding?: { logo?: string; color?: string; company?: string };
  }) => {
    const { title, content, format = "html", language = "de", branding } = payload;

    metadata.set("status", "generating");
    metadata.set("progress", 20);

    const reportPrompt = `Erstelle einen professionellen ${format === "html" ? "HTML" : "Markdown"}-Report.

Titel: ${title}
Sprache: ${language === "de" ? "Deutsch" : "English"}
${branding?.company ? `Unternehmen: ${branding.company}` : ""}

Inhalt:
${content}

${format === "html" ? `Erstelle vollständiges HTML mit:
- Professionelles CSS (inline)
- Primärfarbe: ${branding?.color || "#FE9B7B"}
- Responsive Layout
- Tabellen für Daten
- Executive Summary am Anfang
- Inhaltsverzeichnis` : "Erstelle strukturiertes Markdown mit Überschriften, Listen, Tabellen."}`;

    const result = await generateText({
      model: openai("gpt-4o-mini"),
      prompt: reportPrompt,
      maxTokens: 4000,
    });

    metadata.set("status", "completed");
    metadata.set("progress", 100);

    return {
      title,
      format,
      report: result.text,
      generatedAt: new Date().toISOString(),
      wordCount: result.text.split(/\s+/).length,
    };
  },
});
