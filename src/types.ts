export type ArchetypeId =
  | "cover-kickoff"
  | "contents-isometric"
  | "consulting-executive-summary"
  | "why-what-how-logic"
  | "proposal-need-three-cards"
  | "proposal-scope-integrated"
  | "benchmark-readiness-summary"
  | "double-materiality-or-risk-map"
  | "issue-tree-to-workplan"
  | "tcfd-pillar-diagnosis"
  | "scenario-financial-impact"
  | "sbti-process"
  | "cdp-response-strategy"
  | "climate-scenario-framework"
  | "method-chevron"
  | "integrated-process-map"
  | "inventory-boundary-flow"
  | "reduction-roadmap-analysis"
  | "schedule-gantt"
  | "team-management"
  | "communication-management"
  | "evidence-grid"
  | "work-scope-table"
  | "comparison-matrix"
  | "consulting-one-page-memo"
  | "regulatory-timeline-radar"
  | "disclosure-taxonomy-map"
  | "peer-good-practice-benchmark"
  | "asis-tobe-gap-roadmap"
  | "iro-register-map"
  | "data-request-tracker"
  | "report-production-workflow"
  | "score-improvement-levers"
  | "training-curriculum-agenda"
  | "case-study-good-practice"
  | "value-chain-hotspot-map"
  | "assurance-evidence-pack"
  | "impact-factoid-big-number"
  | "traffic-light-scorecard"
  | "bubble-priority-portfolio"
  | "forecast-trend-chart"
  | "funnel-conversion-pipeline"
  | "stakeholder-influence-map"
  | "house-framework"
  | "cycle-loop-pdca"
  | "before-after-delta-bridge"
  | "dashboard-kpi-takeaway"
  | "staircase-maturity-evolution"
  | "waterfall-bridge-analysis"
  | "evidence-to-action-strip";

export interface DeckMeta {
  clientName: string;
  projectTitle: string;
  documentType: string;
  dateLabel: string;
  purpose?: string;
  audience?: string;
  tone?: string;
}

export interface RawSlide {
  index: number;
  title: string;
  body: string;
  bullets: string[];
  forcedArchetypeId?: ArchetypeId;
}

export interface ArchetypeRule {
  id: ArchetypeId;
  label: string;
  description: string;
  structure: string[];
  keywords: string[];
  layoutHint: string;
  safetyRule: string;
}

export interface PlannedSlide extends RawSlide {
  archetype: ArchetypeRule;
  claimTitle: string;
  governingMessage: string;
  sections: string[];
  rationale: string;
  density: "low" | "medium" | "high";
}
