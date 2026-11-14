import { z } from "zod";

export const CARD_KINDS = [
  "feasibility",
  "demand",
  "features",
  "failures",
  "collaborators",
] as const;

export type CardKind = (typeof CARD_KINDS)[number];

export type Source = { id: string; url: string; title: string; snippet?: string };
export type Industry = { id: string; name: string; why: string };
export type Claim = { text: string; sourceIds: string[] };
export type Card = {
  kind: CardKind;
  title: string;
  summary: string;
  claims: Claim[];
};
export type ExploreEvent =
  | { type: "concept"; concept: string; originalIndustry: string }
  | { type: "industry"; industry: Industry }
  | { type: "evidence"; industryId: string | null; sources: Source[] }
  | { type: "card"; card: Card }
  | { type: "error"; stage: string; message: string }
  | { type: "done" };

export type DemoRun = {
  slug: string;
  idea: string;
  events: { at: number; event: ExploreEvent }[]; // at = ms since start
};

const SourceSchema = z.object({
  id: z.string(),
  url: z.string(),
  title: z.string(),
  snippet: z.string().optional(),
});
const IndustrySchema = z.object({ id: z.string(), name: z.string(), why: z.string() });
const ClaimSchema = z.object({ text: z.string(), sourceIds: z.array(z.string()) });
const CardSchema = z.object({
  kind: z.enum(CARD_KINDS),
  title: z.string(),
  summary: z.string(),
  claims: z.array(ClaimSchema),
});

export const ExploreEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("concept"), concept: z.string(), originalIndustry: z.string() }),
  z.object({ type: z.literal("industry"), industry: IndustrySchema }),
  z.object({
    type: z.literal("evidence"),
    industryId: z.string().nullable(),
    sources: z.array(SourceSchema),
  }),
  z.object({ type: z.literal("card"), card: CardSchema }),
  z.object({ type: z.literal("error"), stage: z.string(), message: z.string() }),
  z.object({ type: z.literal("done") }),
]);

export const DemoRunSchema = z.object({
  slug: z.string(),
  idea: z.string(),
  events: z.array(z.object({ at: z.number(), event: ExploreEventSchema })),
});
