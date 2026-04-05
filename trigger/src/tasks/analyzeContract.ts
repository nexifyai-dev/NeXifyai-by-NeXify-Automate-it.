/**
 * NeXifyAI — Contract Analysis Task
 * AI-Vertragsanalyse mit Risikobewertung.
 */
import { task, metadata } from "@trigger.dev/sdk/v3";
import { generateObject, generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

const ContractAnalysisSchema = z.object({
  contractType: z.string(),
  parties: z.array(z.object({
    name: z.string(),
    role: z.string(),
  })),
  keyTerms: z.array(z.object({
    term: z.string(),
    description: z.string(),
    riskLevel: z.enum(["low", "medium", "high", "critical"]),
  })),
  riskScore: z.number().min(1).max(10),
  missingClauses: z.array(z.string()),
  recommendations: z.array(z.string()),
  jurisdiction: z.string(),
  duration: z.string().optional(),
  totalValue: z.string().optional(),
});

export const analyzeContractTask = task({
  id: "analyze-contract",
  maxDuration: 180,
  retry: { maxAttempts: 2 },
  run: async (payload: {
    contractText: string;
    contractType?: string;
    jurisdiction?: string;
    language?: string;
  }) => {
    const { contractText, contractType = "service", jurisdiction = "DE", language = "de" } = payload;

    metadata.set("status", "analyzing");
    metadata.set("phase", "Vertragsanalyse");
    metadata.set("progress", 10);

    // Step 1: Extract structured data
    metadata.set("phase", "Datenextraktion");
    metadata.set("progress", 20);

    const analysis = await generateObject({
      model: openai("gpt-4o"),
      schema: ContractAnalysisSchema,
      prompt: `Analysiere diesen ${contractType === "service" ? "Dienstleistungsvertrag" : "Vertrag"} (Jurisdiktion: ${jurisdiction}).

Vertragstext:
${contractText.substring(0, 15000)}

Extrahiere:
1. Vertragstyp, Parteien
2. Wesentliche Bestimmungen mit Risikobewertung (low/medium/high/critical)
3. Gesamt-Risikoscore (1-10, 10 = höchstes Risiko)
4. Fehlende Standardklauseln für ${jurisdiction}
5. Empfehlungen

Sprache: ${language === "de" ? "Deutsch" : "English"}`,
    });

    // Step 2: DSGVO/Compliance Check
    metadata.set("phase", "Compliance-Check");
    metadata.set("progress", 60);

    const complianceCheck = await generateText({
      model: openai("gpt-4o"),
      prompt: `Prüfe diesen Vertrag auf ${jurisdiction === "DE" ? "DSGVO und deutsches Recht" : "datenschutzrechtliche"} Compliance:

${contractText.substring(0, 10000)}

Prüfe insbesondere:
- Auftragsverarbeitungsvertrag (AVV) vorhanden?
- Datenschutzklauseln ausreichend?
- Haftungsbegrenzungen angemessen?
- Kündigungsfristen gesetzeskonform?
- Gerichtsstand korrekt?

Erstelle einen strukturierten Compliance-Bericht.`,
    });

    // Step 3: Executive Summary
    metadata.set("phase", "Executive Summary");
    metadata.set("progress", 85);

    const summary = await generateText({
      model: openai("gpt-4o-mini"),
      prompt: `Erstelle ein Executive Summary (max 200 Wörter) für diese Vertragsanalyse:
Risikoscore: ${analysis.object.riskScore}/10
Parteien: ${analysis.object.parties.map((p) => `${p.name} (${p.role})`).join(", ")}
Kritische Punkte: ${analysis.object.keyTerms.filter((t) => t.riskLevel === "critical" || t.riskLevel === "high").length}
Fehlende Klauseln: ${analysis.object.missingClauses.length}

Sprache: ${language === "de" ? "Deutsch" : "English"}`,
    });

    metadata.set("phase", "Abgeschlossen");
    metadata.set("progress", 100);
    metadata.set("status", "completed");

    return {
      analysis: analysis.object,
      complianceReport: complianceCheck.text,
      executiveSummary: summary.text,
      analyzedAt: new Date().toISOString(),
    };
  },
});
