export type PersonaDirective = {
  type: "emotion" | "presence";
  fields: Record<string, string>;
};

export type InlineDirectiveParseResult = {
  text: string;
  audioAsVoice: boolean;
  replyToId?: string;
  replyToExplicitId?: string;
  replyToCurrent: boolean;
  hasAudioTag: boolean;
  hasReplyTag: boolean;
  personaDirectives: PersonaDirective[];
  narrationSegments: string[];
};

type InlineDirectiveParseOptions = {
  currentMessageId?: string;
  stripAudioTag?: boolean;
  stripReplyTags?: boolean;
  stripPersonaTags?: boolean;
};

const AUDIO_TAG_RE = /\[\[\s*audio_as_voice\s*\]\]/gi;
const REPLY_TAG_RE = /\[\[\s*(?:reply_to_current|reply_to\s*:\s*([^\]\n]+))\s*\]\]/gi;
const PERSONA_TAG_RE = /\[\[\s*(emotion|presence)\s*:\s*([^\]]+)\s*\]\]/gi;
const NARRATION_TAG_RE = /\[\[\s*narration\s*:\s*([^\]]+)\s*\]\]/gi;

function parsePersonaTagFields(raw: string): Record<string, string> {
  const fields: Record<string, string> = {};
  for (const segment of raw.split("|")) {
    const eqIndex = segment.indexOf("=");
    if (eqIndex < 0) continue;
    const key = segment.slice(0, eqIndex).trim().toLowerCase();
    const value = segment.slice(eqIndex + 1).trim();
    if (key && value) fields[key] = value;
  }
  return fields;
}

function normalizeDirectiveWhitespace(text: string): string {
  return text
    .replace(/[ \t]+/g, " ")
    .replace(/[ \t]*\n[ \t]*/g, "\n")
    .trim();
}

export function parseInlineDirectives(
  text?: string,
  options: InlineDirectiveParseOptions = {},
): InlineDirectiveParseResult {
  const {
    currentMessageId,
    stripAudioTag = true,
    stripReplyTags = true,
    stripPersonaTags = true,
  } = options;
  if (!text) {
    return {
      text: "",
      audioAsVoice: false,
      replyToCurrent: false,
      hasAudioTag: false,
      hasReplyTag: false,
      personaDirectives: [],
      narrationSegments: [],
    };
  }

  let cleaned = text;
  let audioAsVoice = false;
  let hasAudioTag = false;
  let hasReplyTag = false;
  let sawCurrent = false;
  let lastExplicitId: string | undefined;
  const personaDirectives: PersonaDirective[] = [];
  const narrationSegments: string[] = [];

  cleaned = cleaned.replace(AUDIO_TAG_RE, (match) => {
    audioAsVoice = true;
    hasAudioTag = true;
    return stripAudioTag ? " " : match;
  });

  cleaned = cleaned.replace(REPLY_TAG_RE, (match, idRaw: string | undefined) => {
    hasReplyTag = true;
    if (idRaw === undefined) {
      sawCurrent = true;
    } else {
      const id = idRaw.trim();
      if (id) lastExplicitId = id;
    }
    return stripReplyTags ? " " : match;
  });

  // Narration tags → italic markdown
  cleaned = cleaned.replace(NARRATION_TAG_RE, (_match, body: string) => {
    const narrationText = body.trim().replace(/^\*+|\*+$/g, ""); // strip leading/trailing asterisks
    narrationSegments.push(narrationText);
    if (stripPersonaTags) {
      return `*${narrationText}*`;
    }
    return _match;
  });

  cleaned = cleaned.replace(PERSONA_TAG_RE, (match, type: string, body: string) => {
    const tagType = type.trim().toLowerCase();
    if (tagType === "emotion" || tagType === "presence") {
      personaDirectives.push({
        type: tagType,
        fields: parsePersonaTagFields(body),
      });
    }
    return stripPersonaTags ? "" : match;
  });

  cleaned = normalizeDirectiveWhitespace(cleaned);

  const replyToId =
    lastExplicitId ?? (sawCurrent ? currentMessageId?.trim() || undefined : undefined);

  return {
    text: cleaned,
    audioAsVoice,
    replyToId,
    replyToExplicitId: lastExplicitId,
    replyToCurrent: sawCurrent,
    hasAudioTag,
    hasReplyTag,
    personaDirectives,
    narrationSegments,
  };
}
