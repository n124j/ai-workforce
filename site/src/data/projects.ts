import type { Project } from "../lib/validateProjects";

export const projects: Project[] = [
  {
    slug: "eval-first-rag",
    title: "Eval-first agentic RAG",
    summary:
      "Planned: hybrid keyword and vector retrieval with reranking, scored by an evaluation harness that runs as a CI gate.",
    status: "planned",
    repo_url: "",
  },
  {
    slug: "multi-agent-hitl",
    title: "Multi-agent orchestrator with human-in-the-loop",
    summary:
      "Planned: a supervisor coordinating specialist agents with durable state, confidence-based escalation, approval gates and an audit trail.",
    status: "planned",
    repo_url: "",
  },
  {
    slug: "claude-code-agents",
    title: "Claude Code engineering agents",
    summary:
      "Planned: open-source agents and an MCP server for code review, deployment validation and doc generation, packaged as a GitHub Action.",
    status: "planned",
    repo_url: "",
  },
  {
    slug: "metadata-governance",
    title: "LLM metadata enrichment and governance",
    summary:
      "Planned: a pipeline that classifies and enriches data-catalog metadata with an LLM, with PII detection and privacy guardrails, on synthetic data.",
    status: "planned",
    repo_url: "",
  },
  {
    slug: "llm-gateway",
    title: "LLM gateway with observability and guardrails",
    summary:
      "Planned: a proxy in front of multiple model providers with routing, caching, cost tracking, guardrails and Prometheus and Grafana dashboards.",
    status: "planned",
    repo_url: "",
  },
];
