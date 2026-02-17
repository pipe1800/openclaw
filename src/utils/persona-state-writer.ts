/**
 * Persona State Writer
 *
 * Processes persona directives (emotion, presence) extracted from assistant
 * responses and writes them to workspace state files.
 *
 * State files:
 *   - memory/emotion-state.json  — emotional state with inertia model
 *   - memory/presence-state.json — physical presence (location, outfit, posture)
 */

import { writeFile, readFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import { homedir } from "node:os";
import type { PersonaDirective } from "./directive-tags.js";

// ─── Emotion Inertia Model ───────────────────────────────────────────────────

const DEFAULT_INERTIA = 0.4; // How much the previous emotion persists (0 = instant switch, 1 = never changes)
const HIGH_AROUSAL_INERTIA = 0.25; // Faster transitions for high-arousal emotions
const LOW_AROUSAL_INERTIA = 0.55; // Slower transitions for low-arousal states
const HISTORY_LIMIT = 50;

type EmotionEntry = {
  primary: string;
  secondary: string | null;
  valence: number;
  arousal: number;
  confidence: number;
  since: string;
  trigger?: string;
};

type EmotionState = {
  _meta: Record<string, unknown>;
  current: EmotionEntry;
  previous: Partial<EmotionEntry> & { transitioned_at?: string };
  history: Array<EmotionEntry & { ended_at: string }>;
  session_arc: {
    start_emotion: string;
    peak_valence: number;
    peak_arousal: number;
    current_trend: string;
  };
  patterns: Record<string, unknown>;
  taxonomy: Record<string, unknown>;
};

type PresenceState = {
  _meta: Record<string, unknown>;
  location: {
    room_key: string;
    label: string;
    zone: string;
  };
  appearance: {
    outfit_key: string;
    posture: string;
    clothing: string;
    accessories: string[];
    hair: string;
    footwear: string;
  };
  last_transition: {
    from: string | null;
    to: string;
    narration: string;
    timestamp: string;
  };
  idle_since: string | null;
  updated_at: string;
};

// ─── File I/O ────────────────────────────────────────────────────────────────

async function readJsonFile<T>(filePath: string): Promise<T | null> {
  try {
    const content = await readFile(filePath, "utf-8");
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

async function writeJsonFile(filePath: string, data: unknown): Promise<void> {
  try {
    await writeFile(filePath, JSON.stringify(data, null, 2) + "\n", "utf-8");
  } catch (err) {
    console.error(`[persona-state] Failed to write ${filePath}:`, err instanceof Error ? err.message : String(err));
  }
}

// ─── Emotion Processing ─────────────────────────────────────────────────────

function computeInertia(arousal: number): number {
  if (arousal > 0.6) return HIGH_AROUSAL_INERTIA;
  if (arousal < 0.3) return LOW_AROUSAL_INERTIA;
  return DEFAULT_INERTIA;
}

function blendValue(current: number, target: number, inertia: number): number {
  return current * inertia + target * (1 - inertia);
}

function determineTrend(history: Array<{ valence: number }>, current: number): string {
  if (history.length < 2) return "stable";
  const recent = history.slice(-3);
  const avgRecent = recent.reduce((sum, e) => sum + e.valence, 0) / recent.length;
  const delta = current - avgRecent;
  if (delta > 0.15) return "rising-positive";
  if (delta < -0.15) return "falling-negative";
  if (current > 0.3) return "stable-positive";
  if (current < -0.3) return "stable-negative";
  return "stable";
}

async function processEmotionDirective(
  workspaceDir: string,
  fields: Record<string, string>,
): Promise<void> {
  const filePath = join(workspaceDir, "memory", "emotion-state.json");
  const state = await readJsonFile<EmotionState>(filePath);
  if (!state) return;

  const newName = fields.name ?? fields.emotion;
  if (!newName) return;

  const newValence = fields.valence !== undefined ? parseFloat(fields.valence) : undefined;
  const newArousal = fields.arousal !== undefined ? parseFloat(fields.arousal) : undefined;
  const newConfidence = fields.confidence !== undefined ? parseFloat(fields.confidence) : undefined;
  const newSecondary = fields.secondary ?? null;

  // Resolve primary emotion from taxonomy
  let primary = newName;
  let foundInTaxonomy = false;
  if (state.taxonomy) {
    const primaries = state.taxonomy.primaries as Record<string, unknown> | undefined;
    const secondaries = state.taxonomy.secondaries as Record<string, string[]> | undefined;
    const lowerName = newName.toLowerCase();

    // Check if it's a primary emotion directly
    if (primaries && lowerName in primaries) {
      primary = lowerName;
      foundInTaxonomy = true;
    }
    // Check if it's a secondary emotion → resolve to its primary
    if (!foundInTaxonomy && secondaries) {
      for (const [prim, secs] of Object.entries(secondaries)) {
        if (secs.map((s) => s.toLowerCase()).includes(lowerName)) {
          primary = prim;
          foundInTaxonomy = true;
          break;
        }
      }
    }
    // Check compound emotions
    if (!foundInTaxonomy && state.taxonomy.compounds) {
      const compounds = state.taxonomy.compounds as Record<string, string[]>;
      if (lowerName in compounds) {
        // Use the first component as primary
        primary = compounds[lowerName]![0] ?? "neutral";
        foundInTaxonomy = true;
      }
    }
    // Fallback: use closest primary by trying to match partial names
    if (!foundInTaxonomy && primaries) {
      const primaryKeys = Object.keys(primaries);
      // Check if the emotion name contains a primary (e.g., "romantic love" → "love")
      const match = primaryKeys.find((pk) => lowerName.includes(pk) || pk.includes(lowerName));
      if (match) {
        primary = match;
        foundInTaxonomy = true;
      }
    }
    // Ultimate fallback: map to nearest known primary by valence/arousal
    if (!foundInTaxonomy && primaries) {
      if (newValence !== undefined) {
        primary = newValence >= 0.3 ? "joy" : newValence <= -0.3 ? "sadness" : "neutral";
      } else {
        primary = "neutral";
      }
    }
  }

  const now = new Date().toISOString();

  // Apply inertia blending
  const currentArousal = state.current?.arousal ?? 0;
  const currentValence = state.current?.valence ?? 0;
  const inertia = computeInertia(newArousal ?? currentArousal);

  const blendedValence = newValence !== undefined
    ? blendValue(currentValence, newValence, inertia)
    : currentValence;
  const blendedArousal = newArousal !== undefined
    ? blendValue(currentArousal, newArousal, inertia)
    : currentArousal;

  // Archive current → previous
  if (state.current) {
    state.previous = {
      primary: state.current.primary,
      secondary: state.current.secondary,
      valence: state.current.valence,
      arousal: state.current.arousal,
      transitioned_at: now,
    };

    // Push to history (with limit)
    state.history = state.history ?? [];
    state.history.push({
      ...state.current,
      ended_at: now,
    });
    if (state.history.length > HISTORY_LIMIT) {
      state.history = state.history.slice(-HISTORY_LIMIT);
    }
  }

  // Set new current
  state.current = {
    primary,
    secondary: newSecondary ?? (foundInTaxonomy && primary !== newName.toLowerCase() ? newName.toLowerCase() : null),
    valence: Math.round(blendedValence * 1000) / 1000,
    arousal: Math.round(blendedArousal * 1000) / 1000,
    confidence: newConfidence ?? 0.8,
    since: now,
    trigger: fields.trigger,
  };

  // Update session arc
  state.session_arc = {
    start_emotion: state.session_arc?.start_emotion ?? primary,
    peak_valence: Math.max(state.session_arc?.peak_valence ?? -1, blendedValence),
    peak_arousal: Math.max(state.session_arc?.peak_arousal ?? 0, blendedArousal),
    current_trend: determineTrend(state.history, blendedValence),
  };

  // Update meta
  state._meta = { ...state._meta, last_updated: now.split("T")[0] };

  await writeJsonFile(filePath, state);
}

// ─── Presence Processing ─────────────────────────────────────────────────────

async function processPresenceDirective(
  workspaceDir: string,
  fields: Record<string, string>,
): Promise<void> {
  const filePath = join(workspaceDir, "memory", "presence-state.json");
  const state = await readJsonFile<PresenceState>(filePath);
  if (!state) return;

  const now = new Date().toISOString();
  let changed = false;

  // Location update
  if (fields.location && fields.location.toLowerCase() !== "unchanged") {
    const oldLocation = state.location?.label ?? null;
    // Try to match room key from label
    const roomKey = fields.location.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    state.location = {
      room_key: roomKey,
      label: fields.location,
      zone: fields.zone ?? state.location?.zone ?? "",
    };
    state.last_transition = {
      from: oldLocation,
      to: fields.location,
      narration: fields.narration ?? `Moved to ${fields.location}`,
      timestamp: now,
    };
    changed = true;
  }

  // Posture update
  if (fields.posture && fields.posture.toLowerCase() !== "unchanged") {
    state.appearance = state.appearance ?? {} as PresenceState["appearance"];
    state.appearance.posture = fields.posture;
    changed = true;
  }

  // Clothing update
  if (fields.clothing && fields.clothing.toLowerCase() !== "unchanged") {
    state.appearance = state.appearance ?? {} as PresenceState["appearance"];
    state.appearance.clothing = fields.clothing;
    changed = true;
  }

  // Hair update
  if (fields.hair && fields.hair.toLowerCase() !== "unchanged") {
    state.appearance = state.appearance ?? {} as PresenceState["appearance"];
    state.appearance.hair = fields.hair;
    changed = true;
  }

  // Accessories update
  if (fields.accessories && fields.accessories.toLowerCase() !== "unchanged") {
    state.appearance = state.appearance ?? {} as PresenceState["appearance"];
    state.appearance.accessories = fields.accessories.split(",").map((s) => s.trim()).filter(Boolean);
    changed = true;
  }

  // Outfit key update
  if (fields.outfit) {
    state.appearance = state.appearance ?? {} as PresenceState["appearance"];
    state.appearance.outfit_key = fields.outfit;
    changed = true;
  }

  if (changed) {
    state.updated_at = now;
    state.idle_since = null;
    state._meta = { ...state._meta, last_updated: now.split("T")[0] };
    await writeJsonFile(filePath, state);
  }
}

// ─── Canvas State Writer ─────────────────────────────────────────────────────

/**
 * Write combined canvas state to the canvas host root directory.
 * This file is polled by the canvas HTML to update the visual display.
 */
async function writeCanvasState(
  workspaceDir: string,
  narrationSegments?: string[],
): Promise<void> {
  try {
    const canvasRoot = join(homedir(), ".openclaw", "canvas");
    await mkdir(canvasRoot, { recursive: true });

    const emotionState = await readJsonFile<EmotionState>(
      join(workspaceDir, "memory", "emotion-state.json"),
    );
    const presenceState = await readJsonFile<PresenceState>(
      join(workspaceDir, "memory", "presence-state.json"),
    );

    const canvasState: Record<string, unknown> = {
      emotion: emotionState?.current
        ? {
            name: emotionState.current.secondary ?? emotionState.current.primary,
            primary: emotionState.current.primary,
            valence: emotionState.current.valence,
            arousal: emotionState.current.arousal,
          }
        : null,
      presence: presenceState
        ? {
            room: presenceState.location?.room_key ?? null,
            roomLabel: presenceState.location?.label ?? null,
            background: await resolveBackground(workspaceDir, presenceState.location?.room_key),
            posture: presenceState.appearance?.posture ?? null,
            clothing: presenceState.appearance?.clothing ?? null,
          }
        : null,
      narration: narrationSegments?.length
        ? narrationSegments[narrationSegments.length - 1]
        : null,
      timestamp: new Date().toISOString(),
    };

    await writeJsonFile(join(canvasRoot, "state.json"), canvasState);
  } catch (err) {
    // Non-critical — don't let canvas state writing break the main flow
    console.error(
      `[persona-state] Canvas state write failed:`,
      err instanceof Error ? err.message : String(err),
    );
  }
}

/**
 * Resolve background filename from room key using rockwood-rooms.json
 */
async function resolveBackground(
  workspaceDir: string,
  roomKey?: string,
): Promise<string | null> {
  if (!roomKey) return null;
  try {
    const rooms = await readJsonFile<{ rooms: Record<string, { background?: string }> }>(
      join(workspaceDir, "memory", "rockwood-rooms.json"),
    );
    if (!rooms?.rooms) return null;
    // Direct match
    if (rooms.rooms[roomKey]?.background) return rooms.rooms[roomKey]!.background!;
    // Fuzzy match: normalize both keys (strip apostrophe-dashes, etc.)
    const normalize = (k: string) => k.replace(/[^a-z0-9]/gi, "").toLowerCase();
    const normalizedKey = normalize(roomKey);
    for (const [k, v] of Object.entries(rooms.rooms)) {
      if (normalize(k) === normalizedKey && v.background) return v.background;
    }
    return null;
  } catch {
    return null;
  }
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Process persona directives extracted from an assistant response.
 * Writes emotion and presence state to workspace files.
 *
 * @param workspaceDir - Absolute path to the agent workspace
 * @param directives - Parsed persona directives from the response
 */
export async function processPersonaDirectives(
  workspaceDir: string,
  directives: PersonaDirective[],
  narrationSegments?: string[],
): Promise<void> {
  if ((!directives.length && !narrationSegments?.length) || !workspaceDir) return;

  const tasks: Promise<void>[] = [];

  for (const directive of directives) {
    if (directive.type === "emotion") {
      tasks.push(processEmotionDirective(workspaceDir, directive.fields));
    } else if (directive.type === "presence") {
      tasks.push(processPresenceDirective(workspaceDir, directive.fields));
    }
  }

  // Wait for emotion/presence state files to be written first
  await Promise.allSettled(tasks);

  // Then write combined canvas state (reads the freshly-written state files)
  await writeCanvasState(workspaceDir, narrationSegments);
}
