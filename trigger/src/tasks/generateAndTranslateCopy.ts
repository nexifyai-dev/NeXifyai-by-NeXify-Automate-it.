/**
 * NeXifyAI — Generate and Translate Copy Task
 * Prompt Chaining: Generate -> Validate -> Translate.
 */
import { task, metadata } from "@trigger.dev/sdk/v3";
import { generateText, generateObject } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

const ValidationSchema = z.object({
  isValid: z.boolean(),
  qualityScore: z.number().min(1).max(10),
  issues: z.array(z.string()),
  suggestions: z.array(z.string()),
});

export const generateAndTranslateCopyTask = task({
  id: "generate-and-translate-copy",
  maxDuration: 180,
  retry: { maxAttempts: 2 },
  run: async (payload: {
    brief: string;
    tone?: string;
    targetLanguages?: string[];
    maxLength?: number;
  }) => {
    const { brief, tone = "professional", targetLanguages = ["en"], maxLength = 500 } = payload;

    // Step 1: Generate
    metadata.set("phase", "Generierung");
    metadata.set("progress", 10);

    const generated = await generateText({
      model: openai("gpt-4o-mini"),
      prompt: `Erstelle professionellen Marketing-Copy auf Deutsch.
Brief: ${brief}
Tonalität: ${tone}
Maximale Länge: ${maxLength} Wörter
Erstelle: Headline, Subheadline, Body-Text, Call-to-Action.`,
    });

    // Step 2: Validate
    metadata.set("phase", "Validierung");
    metadata.set("progress", 40);

    const validation = await generateObject({
      model: openai("gpt-4o-mini"),
      schema: ValidationSchema,
      prompt: `Bewerte diesen Marketing-Copy:
"${generated.text}"

Brief war: ${brief}
Tonalität soll sein: ${tone}

Bewerte: Qualität (1-10), Probleme, Verbesserungsvorschläge.`,
    });

    // Step 3: Improve if needed
    let finalCopy = generated.text;
    if (validation.object.qualityScore < 7 && validation.object.suggestions.length > 0) {
      metadata.set("phase", "Optimierung");
      metadata.set("progress", 55);

      const improved = await generateText({
        model: openai("gpt-4o-mini"),
        prompt: `Verbessere diesen Marketing-Copy basierend auf dem Feedback:
Original: "${generated.text}"
Feedback: ${validation.object.suggestions.join(", ")}
Behalte die Struktur (Headline, Subheadline, Body, CTA) bei.`,
      });
      finalCopy = improved.text;
    }

    // Step 4: Translate
    metadata.set("phase", "Übersetzung");
    metadata.set("progress", 70);

    const translations: Record<string, string> = { de: finalCopy };

    for (const lang of targetLanguages) {
      if (lang === "de") continue;
      const langNames: Record<string, string> = { en: "Englisch", fr: "Französisch", es: "Spanisch", it: "Italienisch" };
      const translated = await generateText({
        model: openai("gpt-4o-mini"),
        prompt: `Übersetze diesen Marketing-Copy nach ${langNames[lang] || lang}. Behalte Tonalität und Wirkung bei:\n"${finalCopy}"`,
      });
      translations[lang] = translated.text;
    }

    metadata.set("phase", "Abgeschlossen");
    metadata.set("progress", 100);

    return {
      brief,
      originalCopy: finalCopy,
      validation: validation.object,
      translations,
      languages: Object.keys(translations),
      completedAt: new Date().toISOString(),
    };
  },
});
