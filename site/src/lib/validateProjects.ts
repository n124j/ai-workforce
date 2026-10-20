export type Status = "planned" | "in-progress" | "shipped";

export type Project = {
  slug: string;
  title: string;
  summary: string;
  status: Status;
  repo_url: string;
};

const OWNER_PREFIX = "https://github.com/n124j/";

export function validateProjects(projects: Project[]): string[] {
  const errors: string[] = [];
  const seen = new Set<string>();

  for (const p of projects) {
    if (seen.has(p.slug)) {
      errors.push(`Duplicate slug: "${p.slug}"`);
    }
    seen.add(p.slug);

    if (!p.title.trim()) {
      errors.push(`Project "${p.slug}": title must not be empty`);
    }
    if (!p.summary.trim()) {
      errors.push(`Project "${p.slug}": summary must not be empty`);
    }
    if (p.status === "shipped" && !p.repo_url.startsWith(OWNER_PREFIX)) {
      errors.push(
        `Project "${p.slug}": shipped requires repo_url starting with ${OWNER_PREFIX}`,
      );
    }
    if (p.status === "planned" && p.repo_url !== "") {
      errors.push(`Project "${p.slug}": repo_url must be empty for planned projects`);
    }
  }

  return errors;
}
