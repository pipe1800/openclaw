import * as fs from "node:fs/promises";
import * as path from "node:path";
import { resolveAgentWorkspaceDir, resolveDefaultAgentId } from "../../agents/agent-scope.js";
import { loadConfig } from "../../config/config.js";
import { ErrorCodes, errorShape } from "../protocol/index.js";
import type { GatewayRequestHandlers } from "./types.js";

const MAX_FILE_SIZE = 1024 * 1024; // 1MB max

function isWithinWorkspace(filePath: string, workspace: string): boolean {
  const resolved = path.resolve(workspace, filePath);
  return resolved.startsWith(path.resolve(workspace));
}

export const fileHandlers: GatewayRequestHandlers = {
  "file.read": async ({ params, respond }) => {
    const filePath = params.path as string | undefined;
    if (!filePath || typeof filePath !== "string") {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "missing path parameter"));
      return;
    }

    const cfg = loadConfig();
    const workspace = resolveAgentWorkspaceDir(cfg, resolveDefaultAgentId(cfg));
    if (!workspace) {
      respond(false, undefined, errorShape(ErrorCodes.UNAVAILABLE, "workspace not configured"));
      return;
    }

    // Security: only allow reads within workspace
    if (!isWithinWorkspace(filePath, workspace)) {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "path must be within workspace"));
      return;
    }

    const fullPath = path.resolve(workspace, filePath);

    try {
      const stat = await fs.stat(fullPath);
      if (stat.size > MAX_FILE_SIZE) {
        respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, `file too large (max ${MAX_FILE_SIZE} bytes)`));
        return;
      }
      const content = await fs.readFile(fullPath, "utf-8");
      respond(true, { content });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      respond(false, undefined, errorShape(ErrorCodes.UNAVAILABLE, msg));
    }
  },

  "file.write": async ({ params, respond }) => {
    const filePath = params.path as string | undefined;
    const content = params.content as string | undefined;

    if (!filePath || typeof filePath !== "string") {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "missing path parameter"));
      return;
    }
    if (content === undefined || typeof content !== "string") {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "missing content parameter"));
      return;
    }

    const cfg = loadConfig();
    const workspace = resolveAgentWorkspaceDir(cfg, resolveDefaultAgentId(cfg));
    if (!workspace) {
      respond(false, undefined, errorShape(ErrorCodes.UNAVAILABLE, "workspace not configured"));
      return;
    }

    // Security: only allow writes within workspace
    if (!isWithinWorkspace(filePath, workspace)) {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "path must be within workspace"));
      return;
    }

    const fullPath = path.resolve(workspace, filePath);

    try {
      // Ensure parent directory exists
      await fs.mkdir(path.dirname(fullPath), { recursive: true });
      await fs.writeFile(fullPath, content, "utf-8");
      respond(true, { success: true });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      respond(false, undefined, errorShape(ErrorCodes.UNAVAILABLE, msg));
    }
  },
};
