import { describe, expect, test } from "vitest";
import { validateProjects, type Project } from "../src/lib/validateProjects";
import { projects } from "../src/data/projects";

const base: Project = {
  slug: "a",
  title: "A",
  summary: "Summary of A.",
  status: "planned",
  repo_url: "",
};

describe("validateProjects", () => {
  test("test_shipped_requires_repo_url", () => {
    const errors = validateProjects([{ ...base, status: "shipped", repo_url: "" }]);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors.some((e) => e.includes("repo_url"))).toBe(true);
  });

  test("test_duplicate_slugs", () => {
    const errors = validateProjects([base, { ...base }]);
    expect(errors.some((e) => e.toLowerCase().includes("duplicate"))).toBe(true);
  });

  test("test_planned_with_url_is_invalid", () => {
    const errors = validateProjects([
      { ...base, status: "planned", repo_url: "https://github.com/n124j/x" },
    ]);
    expect(errors.length).toBeGreaterThan(0);
  });

  test("test_empty_list_is_valid", () => {
    expect(validateProjects([])).toEqual([]);
  });

  test("test_default_projects_valid", () => {
    expect(validateProjects(projects)).toEqual([]);
  });

  test("test_non_owner_url_rejected", () => {
    const errors = validateProjects([
      { ...base, status: "shipped", repo_url: "https://github.com/other/x" },
    ]);
    expect(errors.length).toBeGreaterThan(0);
  });
});
