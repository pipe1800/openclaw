/**
 * Auto-select model based on message content analysis.
 * 
 * Detects coding-related tasks and upgrades to a more capable model,
 * while keeping simple conversations on a lighter/cheaper model.
 */

export type ModelAutoSelectConfig = {
  enabled?: boolean;
  /** Default model for casual chat (alias or provider/model) */
  defaultModel?: string;
  /** Model for coding/complex tasks (alias or provider/model) */
  codingModel?: string;
  /** Keywords that trigger coding model */
  keywords?: string[];
};

export type ModelAutoSelectResult = {
  /** Whether auto-selection was applied */
  applied: boolean;
  /** The selected model category */
  category: "default" | "coding";
  /** Reason for the selection */
  reason?: string;
};

/** Default keywords that suggest coding/technical work */
const DEFAULT_CODING_KEYWORDS = [
  "implement",
  "refactor",
  "debug",
  "fix",
  "build",
  "code",
  "function",
  "class",
  "compile",
  "error",
  "bug",
  "test",
  "deploy",
  "commit",
  "merge",
  "pull request",
  "pr",
  "review",
  "typescript",
  "javascript",
  "python",
  "rust",
  "java",
  "api",
  "endpoint",
  "database",
  "query",
  "sql",
  "schema",
  "migration",
];

/** Patterns that indicate code content */
const CODE_FENCE_REGEX = /```[\s\S]*?```/;
const INLINE_CODE_REGEX = /`[^`]+`/g;
const FILE_PATH_REGEX = /(?:^|\s)[.\/]?(?:[\w-]+\/)+[\w.-]+(?:\.[a-z]{1,5})?(?:\s|$)/i;
const IMPORT_REGEX = /(?:^|\s)(?:import|require|from|export)\s+/i;

/**
 * Analyze message content to determine if it's coding-related.
 */
export function analyzeMessageContent(body: string): {
  isCoding: boolean;
  reasons: string[];
} {
  const reasons: string[] = [];
  const bodyLower = body.toLowerCase();

  // Check for code fences
  if (CODE_FENCE_REGEX.test(body)) {
    reasons.push("code fence detected");
  }

  // Check for multiple inline code snippets
  const inlineMatches = body.match(INLINE_CODE_REGEX);
  if (inlineMatches && inlineMatches.length >= 2) {
    reasons.push("multiple inline code references");
  }

  // Check for file paths
  if (FILE_PATH_REGEX.test(body)) {
    reasons.push("file path detected");
  }

  // Check for import statements
  if (IMPORT_REGEX.test(body)) {
    reasons.push("import/require statement");
  }

  // Check for coding keywords
  for (const keyword of DEFAULT_CODING_KEYWORDS) {
    if (bodyLower.includes(keyword.toLowerCase())) {
      reasons.push(`keyword: ${keyword}`);
      break; // One keyword match is enough
    }
  }

  return {
    isCoding: reasons.length > 0,
    reasons,
  };
}

/**
 * Check recent tool context for coding-related activity.
 */
export function analyzeRecentToolContext(recentTools: string[]): {
  isCoding: boolean;
  reasons: string[];
} {
  const reasons: string[] = [];
  const codingTools = ["exec", "read", "write", "edit"];

  for (const tool of recentTools) {
    if (codingTools.includes(tool)) {
      reasons.push(`recent ${tool} tool use`);
    }
  }

  return {
    isCoding: reasons.length >= 2, // Need multiple tool uses to suggest coding context
    reasons,
  };
}

/**
 * Determine if auto-selection should apply and which model to use.
 */
export function resolveModelAutoSelect(params: {
  body: string;
  config?: ModelAutoSelectConfig;
  hasExplicitModelDirective: boolean;
  recentTools?: string[];
}): ModelAutoSelectResult {
  // Skip if disabled or explicit model directive present
  if (!params.config?.enabled || params.hasExplicitModelDirective) {
    return { applied: false, category: "default" };
  }

  // Skip if no coding model configured
  if (!params.config.codingModel) {
    return { applied: false, category: "default" };
  }

  const contentAnalysis = analyzeMessageContent(params.body);
  const toolAnalysis = params.recentTools
    ? analyzeRecentToolContext(params.recentTools)
    : { isCoding: false, reasons: [] };

  const allReasons = [...contentAnalysis.reasons, ...toolAnalysis.reasons];
  const isCoding = contentAnalysis.isCoding || toolAnalysis.isCoding;

  if (isCoding) {
    return {
      applied: true,
      category: "coding",
      reason: allReasons[0], // Primary reason
    };
  }

  return {
    applied: true,
    category: "default",
    reason: "casual conversation",
  };
}

/**
 * Resolve the actual model string based on auto-selection result.
 */
export function resolveAutoSelectedModel(params: {
  result: ModelAutoSelectResult;
  config?: ModelAutoSelectConfig;
  fallbackDefault: string;
}): string | undefined {
  if (!params.result.applied || !params.config) {
    return undefined;
  }

  if (params.result.category === "coding" && params.config.codingModel) {
    return params.config.codingModel;
  }

  if (params.result.category === "default" && params.config.defaultModel) {
    return params.config.defaultModel;
  }

  return undefined;
}
