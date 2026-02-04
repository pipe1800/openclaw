// Character data controller - loads/saves CHARACTER.json from workspace

import type { GatewayBrowserClient } from "../gateway.js";

export interface CharacterTrait {
  name: string;
  description: string;
}

export interface CharacterLimitation {
  name: string;
  description: string;
}

export interface CharacterTrigger {
  trigger: string;
  description: string;
}

export interface CharacterPhysical {
  build: string;
  hair: string;
  eyes: string;
  curves: string;
  style: string;
}

export interface CharacterTonePalette {
  baseline: string;
  swearing: string;
  flirting: string;
  technical: string;
  intimate: string;
}

export interface CharacterPersonality {
  archetypes: string[];
  description: string;
}

export interface CharacterData {
  name: string;
  mission: string;
  personality: CharacterPersonality;
  origin_story: string;
  traits: CharacterTrait[];
  tone_palette: CharacterTonePalette;
  vocabulary_guidelines: string[];
  limitations: CharacterLimitation[];
  escalation_triggers: CharacterTrigger[];
  physical_attributes: CharacterPhysical;
}

export function createEmptyCharacter(): CharacterData {
  return {
    name: "",
    mission: "",
    personality: {
      archetypes: [],
      description: "",
    },
    origin_story: "",
    traits: [],
    tone_palette: {
      baseline: "",
      swearing: "",
      flirting: "",
      technical: "",
      intimate: "",
    },
    vocabulary_guidelines: [],
    limitations: [],
    escalation_triggers: [],
    physical_attributes: {
      build: "",
      hair: "",
      eyes: "",
      curves: "",
      style: "",
    },
  };
}

export type CharacterState = {
  client: GatewayBrowserClient | null;
  connected: boolean;
  characterLoading: boolean;
  characterSaving: boolean;
  characterData: CharacterData | null;
  characterExists: boolean;
  characterError: string | null;
  characterDirty: boolean;
};

export async function loadCharacter(state: CharacterState): Promise<void> {
  if (!state.client || !state.connected) return;
  state.characterLoading = true;
  state.characterError = null;

  try {
    const result = (await state.client.request("file.read", {
      path: "CHARACTER.json",
    })) as { content?: string; error?: string };

    if (result.error) {
      // File doesn't exist yet - that's fine
      if (result.error.includes("ENOENT") || result.error.includes("not found")) {
        state.characterData = createEmptyCharacter();
        state.characterExists = false;
        return;
      }
      state.characterError = result.error;
      return;
    }

    const content = result.content ?? "";
    if (content) {
      state.characterData = JSON.parse(content) as CharacterData;
      state.characterExists = true;
    } else {
      state.characterData = createEmptyCharacter();
      state.characterExists = false;
    }
  } catch (err) {
    state.characterError = err instanceof Error ? err.message : String(err);
    state.characterData = createEmptyCharacter();
    state.characterExists = false;
  } finally {
    state.characterLoading = false;
    state.characterDirty = false;
  }
}

export async function saveCharacter(state: CharacterState): Promise<boolean> {
  if (!state.client || !state.connected || !state.characterData) return false;
  state.characterSaving = true;
  state.characterError = null;

  try {
    const content = JSON.stringify(state.characterData, null, 2);
    const result = (await state.client.request("file.write", {
      path: "CHARACTER.json",
      content,
    })) as { error?: string };

    if (result.error) {
      state.characterError = result.error;
      return false;
    }

    state.characterExists = true;
    state.characterDirty = false;
    return true;
  } catch (err) {
    state.characterError = err instanceof Error ? err.message : String(err);
    return false;
  } finally {
    state.characterSaving = false;
  }
}
